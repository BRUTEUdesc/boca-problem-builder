/*
 * interact - liga um interactor (testlib) e a solucao do time por dois pipes anonimos.
 *
 *   interactor stdout --pipe A--> stdin  da solucao
 *   solucao   stdout --pipe B--> stdin  do interactor
 *
 * Nenhum processo intermediario copia dados: o launcher cria os pipes, faz fork/exec dos dois
 * lados, fecha as suas copias e so espera (wait4). Cada round-trip custa 2 write + 2 read e
 * 2 trocas de contexto, o minimo possivel com processos separados.
 *
 * A solucao normalmente e o proprio safeexec do BOCA (opcao -S), que herda os pipes como
 * stdin/stdout (sem -i/-o) e aplica TL de CPU, TL de relogio (-T), memoria, chroot e uid.
 * O interactor roda fora da jaula (root ou -u/-G), com limites proprios de CPU, memoria e
 * tamanho de arquivo (tout).
 *
 * Uso: interact [opcoes] -- INTERACTOR [args...] -- SOLUCAO [args...]
 *   -w S    teto de relogio de tudo (backstop; mata os dois). Padrao 60
 *   -g S    depois que a solucao termina, o interactor tem S s para terminar. Padrao 5
 *   -c S    limite de CPU do interactor (RLIMIT_CPU). Padrao 10
 *   -m MB   limite de memoria (RLIMIT_AS) do interactor; 0 = sem limite. Padrao 1024
 *   -f KB   limite de arquivo (RLIMIT_FSIZE) do interactor (tout). Padrao 65536
 *   -u UID / -G GID  roda o interactor com esse uid/gid (padrao: o de quem chamou)
 *   -k UID:GID  no fim, mata todo processo desse uid (sobras do time), como o killuser do safeexec
 *   -e ARQ  stderr do interactor (padrao interactor.err)
 *   -o ARQ  resultado key=value (padrao stdout)
 *   -S      a solucao e o safeexec: interpreta o codigo de saida dele (3=TLE, 7=MLE, 2/9=RE...)
 *   -Z      com -S: saida != 0 do programa (safeexec devolve codigo+10) conta como termino normal,
 *           como fazem os templates c/cpp do BOCA
 *   -a CPU  fixa os dois processos nessa CPU (o run/<lang> usa a ultima CPU: round-trip local, sem
 *           acordar outra CPU; ver run/interactive.sh)
 *
 * Codigo de saida do launcher (o run/<lang> traduz para o BOCA):
 *   0  interactor OK e solucao terminou normal (o checker ainda pode rodar sobre o tout)
 *   1  WA dado pelo interactor        2  PE dado pelo interactor
 *   3  erro do juiz: interactor FAIL, crash, morto por limite ou nao terminou
 *   10+X  vale o veredito da solucao; X = codigo do safeexec (13 TLE, 12 RE, 17 MLE, 18, 19...)
 *         sem -S: 12 = RE (sinal/saida != 0), 13 = TLE (backstop)
 *   50 erro interno do launcher
 *
 * Regra do veredito combinado:
 *   1. interactor FAIL (saida 3) -> erro do juiz, sempre (testlib so da FAIL por culpa do juiz).
 *   2. a solucao terminou ANTES do interactor e de forma anormal (TLE/MLE/RE/...) -> veredito da
 *      solucao. O WA/PE do interactor ai e consequencia (EOF inesperado) e e ignorado.
 *   3. o interactor terminou primeiro com WA/PE -> WA/PE, mesmo que depois a solucao morra de
 *      SIGPIPE, leia EOF e estoure o TL etc.
 *   4. o interactor terminou primeiro com OK e depois a solucao foi anormal -> veredito da solucao
 *      (p.ex. respondeu certo e entrou em loop: TLE).
 *   5. solucao normal: vale o interactor (OK/WA/PE); crash/kill do interactor -> erro do juiz.
 * "Quem terminou primeiro" e deterministico: o launcher guarda uma copia das 4 pontas dos pipes e
 * so fecha as de um lado depois de colher (wait4) esse lado. Antes disso o outro lado nao recebe
 * EOF/EPIPE, entao nao tem como "reagir" antes de o launcher registrar a ordem.
 */
#define _GNU_SOURCE
#include <errno.h>
#include <fcntl.h>
#include <sched.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <unistd.h>
#include <grp.h>
#include <sys/resource.h>
#include <sys/time.h>
#include <sys/types.h>
#include <sys/wait.h>

static double now(void) {
	struct timespec t;
	clock_gettime(CLOCK_MONOTONIC, &t);
	return t.tv_sec + t.tv_nsec / 1e9;
}

static double tv(struct timeval t) { return t.tv_sec + t.tv_usec / 1e6; }

struct side {
	pid_t pid;
	int done, status;
	double t_end;
	struct rusage ru;
	int killed; /* morto pelo launcher */
	int order;  /* 1 = terminou primeiro */
};

static void die(const char *m) {
	fprintf(stderr, "interact: %s: %s\n", m, strerror(errno));
	exit(50);
}

static void killuid(int uid, int gid) {
	if (uid <= 0 || gid <= 0 || (uid_t) uid == getuid()) return;
	pid_t k = fork();
	if (k == 0) {
		if (setgroups(0, NULL) || setgid(gid) || setuid(uid) || getuid() != (uid_t) uid) _exit(1);
		kill(-1, SIGKILL);
		_exit(0);
	}
	if (k > 0) while (waitpid(k, NULL, 0) < 0 && errno == EINTR) ;
}

int main(int argc, char **argv) {
	double wall = 60, grace = 5, icpu = 10;
	long imem = 1024, ifsize = 65536;
	int iuid = -1, igid = -1, kuid = -1, kgid = -1, safeexec = 0, zeroknz = 0, cpu = -1;
	const char *ierr = "interactor.err", *outf = NULL;
	int opt;
	while ((opt = getopt(argc, argv, "+w:g:c:m:f:u:G:k:e:o:SZa:")) != -1) {
		switch (opt) {
		case 'w': wall = atof(optarg); break;
		case 'g': grace = atof(optarg); break;
		case 'c': icpu = atof(optarg); break;
		case 'm': imem = atol(optarg); break;
		case 'f': ifsize = atol(optarg); break;
		case 'u': iuid = atoi(optarg); break;
		case 'G': igid = atoi(optarg); break;
		case 'k': if (sscanf(optarg, "%d:%d", &kuid, &kgid) != 2) kuid = kgid = -1; break;
		case 'e': ierr = optarg; break;
		case 'o': outf = optarg; break;
		case 'S': safeexec = 1; break;
		case 'Z': zeroknz = 1; break;
		case 'a': cpu = atoi(optarg); break;
		default: fprintf(stderr, "uso: interact [opcoes] -- INTERACTOR... -- SOLUCAO...\n"); return 50;
		}
	}
	/* getopt com '+' para no primeiro "--" e o consome */
	char **iargv = argv + optind, **sargv = NULL;
	for (int i = optind; i < argc; i++)
		if (!strcmp(argv[i], "--")) { argv[i] = NULL; sargv = argv + i + 1; break; }
	if (!iargv[0] || !sargv || !sargv[0]) {
		fprintf(stderr, "uso: interact [opcoes] -- INTERACTOR... -- SOLUCAO...\n");
		return 50;
	}

	int a[2], b[2]; /* a: interactor -> solucao ; b: solucao -> interactor */
	if (pipe2(a, O_CLOEXEC) || pipe2(b, O_CLOEXEC)) die("pipe2");
	int efd = open(ierr, O_WRONLY | O_CREAT | O_TRUNC | O_CLOEXEC, 0600);
	if (efd < 0) die("open stderr do interactor");

	/* SIGCHLD bloqueado: esperamos com sigtimedwait; os filhos recebem a mascara original */
	sigset_t chld, orig;
	sigemptyset(&chld);
	sigaddset(&chld, SIGCHLD);
	sigprocmask(SIG_BLOCK, &chld, &orig);

	double t0 = now();
	struct side S = {0}, I = {0};

	I.pid = fork();
	if (I.pid < 0) die("fork");
	if (I.pid == 0) {
		setpgid(0, 0);
		sigprocmask(SIG_SETMASK, &orig, NULL);
		/* interactor ignora SIGPIPE: se a solucao morreu, o write falha com EPIPE e o testlib
		   segue ate ler EOF e dar PE, em vez de morrer por sinal (que pareceria crash do juiz) */
		signal(SIGPIPE, SIG_IGN);
		if (dup2(b[0], 0) < 0 || dup2(a[1], 1) < 0 || dup2(efd, 2) < 0) _exit(127);
		if (cpu >= 0) { cpu_set_t c; CPU_ZERO(&c); CPU_SET(cpu, &c); sched_setaffinity(0, sizeof c, &c); }
		struct rlimit r;
		r.rlim_cur = (rlim_t) icpu; r.rlim_max = (rlim_t) icpu + 1; setrlimit(RLIMIT_CPU, &r);
		if (imem > 0) { r.rlim_cur = r.rlim_max = (rlim_t) imem << 20; setrlimit(RLIMIT_AS, &r); }
		r.rlim_cur = r.rlim_max = (rlim_t) ifsize << 10; setrlimit(RLIMIT_FSIZE, &r);
		r.rlim_cur = r.rlim_max = 0; setrlimit(RLIMIT_CORE, &r);
		if (igid > 0 && (setgroups(0, NULL) || setgid(igid))) _exit(126);
		if (iuid > 0 && setuid(iuid)) _exit(126);
		execv(iargv[0], iargv);
		_exit(127);
	}
	S.pid = fork();
	if (S.pid < 0) die("fork");
	if (S.pid == 0) {
		setpgid(0, 0);
		sigprocmask(SIG_SETMASK, &orig, NULL);
		signal(SIGPIPE, SIG_DFL); /* exec herda SIG_IGN; o time tem que poder morrer de SIGPIPE */
		if (dup2(a[0], 0) < 0 || dup2(b[1], 1) < 0) _exit(127);
		if (cpu >= 0) { cpu_set_t c; CPU_ZERO(&c); CPU_SET(cpu, &c); sched_setaffinity(0, sizeof c, &c); }
		execvp(sargv[0], sargv); /* com PATH: o run/<lang> chama "chroot /bocajail ..." */
		_exit(127);
	}
	setpgid(I.pid, I.pid);
	setpgid(S.pid, S.pid);
	close(efd);
	/* O launcher fica com uma copia das 4 pontas e so fecha as do lado que ja colheu. Assim um
	   lado so enxerga o fim do outro (EOF/EPIPE/SIGPIPE) DEPOIS que o launcher registrou quem
	   terminou primeiro: a ordem e deterministica, sem corrida entre os dois wait4. Nao ha copia
	   de dados: o launcher nunca le nem escreve nesses fds. */

	double deadline = t0 + wall, ideadline = 1e300;
	int timedout = 0, seq = 0;
	while (!S.done || !I.done) {
		int st; struct rusage ru; pid_t p;
		while ((p = wait4(-1, &st, WNOHANG, &ru)) > 0) {
			struct side *x = (p == S.pid) ? &S : (p == I.pid) ? &I : NULL;
			if (!x) continue;
			x->done = 1; x->status = st; x->ru = ru; x->t_end = now(); x->order = ++seq;
			if (x == &S) { close(b[1]); close(a[0]); if (!I.done) ideadline = x->t_end + grace; }
			else { close(a[1]); close(b[0]); }
		}
		if (S.done && I.done) break;
		double t = now(), lim = deadline < ideadline ? deadline : ideadline;
		if (t >= lim) {
			if (!I.done) { kill(-I.pid, SIGKILL); I.killed = 1; }
			if (t >= deadline && !S.done) { kill(-S.pid, SIGKILL); S.killed = 1; timedout = 1; }
			if (kuid > 0) killuid(kuid, kgid);
			continue; /* volta para colher */
		}
		double w = lim - t;
		struct timespec ts = { (time_t) w, (long) ((w - (time_t) w) * 1e9) };
		sigtimedwait(&chld, NULL, &ts);
	}
	if (kuid > 0) killuid(kuid, kgid);
	double t1 = now();

	/* ---- classificacao ---- */
	/* solucao: normal? qual codigo BOCA/safeexec? */
	int sol_normal, sol_code; /* sol_code = codigo estilo safeexec */
	char sdesc[64];
	if (WIFEXITED(S.status)) {
		int e = WEXITSTATUS(S.status);
		snprintf(sdesc, sizeof sdesc, "exit %d", e);
		if (safeexec) {
			sol_normal = (e == 0) || (e > 10 && zeroknz);
			sol_code = (e > 10) ? 9 : e;
		} else {
			sol_normal = (e == 0);
			sol_code = e ? 2 : 0;
		}
	} else {
		int sg = WTERMSIG(S.status);
		snprintf(sdesc, sizeof sdesc, "signal %d%s", sg, S.killed ? " (backstop)" : "");
		sol_normal = 0;
		sol_code = S.killed ? 3 : 2;
	}
	if (timedout && !sol_normal) sol_code = 3;

	int int_ok = 0, int_wa = 0, int_pe = 0, int_fail = 0, int_crash = 0;
	char idesc[64];
	if (WIFEXITED(I.status)) {
		int e = WEXITSTATUS(I.status);
		snprintf(idesc, sizeof idesc, "exit %d", e);
		if (e == 0) int_ok = 1;
		else if (e == 1) int_wa = 1;
		else if (e == 2 || e == 4 || e == 8) int_pe = 1; /* PE, dirt, unexpected eof */
		else if (e == 3) int_fail = 1;
		else int_crash = 1;
	} else {
		snprintf(idesc, sizeof idesc, "signal %d%s", WTERMSIG(I.status), I.killed ? " (killed by launcher)" : "");
		int_crash = 1;
	}
	int sol_first = S.order < I.order;

	int rc; const char *verdict;
	static const char *sv[] = {"OK", "CE", "RE", "TLE", "INTERNAL", "PARAM", "INTERNAL", "MLE", "SECURITY", "RE"};
	if (sol_code < 0 || sol_code > 9) sol_code = 9;
	if (int_fail) { rc = 3; verdict = "JUDGE_ERROR"; }                          /* regra 1 */
	else if (!sol_normal && sol_first) { rc = 10 + sol_code; verdict = sv[sol_code]; } /* regra 2 */
	else if (int_crash) { rc = 3; verdict = "JUDGE_ERROR"; }                    /* regra 5 */
	else if (int_wa) { rc = 1; verdict = "WA"; }                                /* regras 3 e 5 */
	else if (int_pe) { rc = 2; verdict = "PE"; }
	else if (int_ok && sol_normal) { rc = 0; verdict = "OK"; }                            /* regra 5 */
	else { rc = 10 + sol_code; verdict = sv[sol_code]; }                        /* regra 4 */

	FILE *o = outf ? fopen(outf, "w") : stdout;
	if (!o) o = stdout;
	fprintf(o, "verdict=%s\nrc=%d\nsolution=%s\ninteractor=%s\nfirst=%s\n", verdict, rc, sdesc, idesc,
	        sol_first ? "solution" : "interactor");
	fprintf(o, "wall=%.3f\nsol_cpu=%.3f\nsol_user=%.3f\nsol_sys=%.3f\nint_cpu=%.3f\n", t1 - t0,
	        tv(S.ru.ru_utime) + tv(S.ru.ru_stime), tv(S.ru.ru_utime), tv(S.ru.ru_stime),
	        tv(I.ru.ru_utime) + tv(I.ru.ru_stime));
	if (o != stdout) fclose(o);
	return rc;
}
