# Biblioteca comum dos run/<lang> de problema INTERATIVO (Polygon + testlib).
# Vai dentro do zip do problema (run/interactive.sh); o run/<lang> a carrega com "unzip -p".
#
# O autojudging.php chama o run/<lang> como root, com cwd = $dir/tmp e:
#   $1 executavel  $2 entrada ($dir/input/X)  $3 TL (total das repeticoes)  $4 repeticoes
#   $5 memoria (MB)  $6 saida maxima (KB)
# O stdout do run vira team/X e o compare/<lang> recebe $1 = team/X, $2 = output/X, $3 = input/X.
#
# Fluxo: o launcher run/interact liga o interactor (fora da jaula, root, com limites de CPU, memoria
# e arquivo) e a solucao (safeexec, jaula, usuario do time) por dois pipes diretos, os dois na mesma
# CPU, e decide quem terminou primeiro. O veredito do interactor vai para $dir/run/verdict.X (root,
# diretorio 0700), que o compare/<lang> le; o stdout do run e o tout do interactor (o checker do
# pacote roda sobre ele). TLE/RE/MLE da solucao saem como codigo de saida do run, como hoje.
#
# A entrada de um interativo e segredo: NAO e copiada para tmp/stdin0 (o run normal copia) e input/
# e run/ ficam 0700 (Java/Python/Kotlin enxergam o /bocajail inteiro, inclusive o diretorio da run).

ia_fail() { echo "interactive: $*"; exit 43; }

# executa o binario sem argumentos (testlib e launcher so imprimem o uso): 126/127 = nao executa
# nesta maquina (formato errado, arquivo corrompido)
ia_runs() {
	timeout -k 2 10 "$1" </dev/null >/dev/null 2>&1
	local r=$?
	[ $r -ne 126 ] && [ $r -ne 127 ]
}

ia_setup() {
	rundir=$(cd "$(dirname "$0")" && pwd) || ia_fail "diretorio run/ nao encontrado"
	dir=$(dirname "$rundir")
	chmod 700 "$rundir" || ia_fail "chmod 700 $rundir"
	[ -d "$dir/input" ] && chmod 700 "$dir/input"
	input="$2"
	base=$(basename "$2")
	verdict="$rundir/verdict.$base"
	tout="$rundir/tout.$base"
	ierr="$rundir/interactor.err.$base"
	ires="$rundir/interact.res.$base"
	rm -f "$verdict" "$tout" "$ierr" "$ires"
	# resposta do juiz (o .a do Polygon) e o 3o argumento do interactor, como no testlib
	ans=()
	[ -f "$dir/output/$base" ] && ans=("$dir/output/$base")

	# TL: o BOCA passa o TL total de N repeticoes; o interativo roda 1 vez com TL/N (o -t do
	# safeexec aceita fracao). Relogio (-T, inteiro): 2*TL+2, para "idle" (os dois esperando) ou
	# solucao sem flush nao prenderem cada teste por TL+30 s como no run normal.
	tl=$(awk -v t="$3" -v r="${4:-1}" 'BEGIN{ if (r < 1) r = 1; if (t <= 0) t = 1; printf "%.3f", t / r }')
	wall=$(awk -v t="$tl" 'BEGIN{ w = int(2 * t + 0.999) + 2; if (w < 3) w = 3; print w }')
	maxm=512000; [ -n "$5" ] && [ "$5" -gt 0 ] && maxm=${5}000
	maxf=1024;   [ -n "$6" ] && [ "$6" -gt 0 ] && maxf=$6
	# memoria do interactor: 2x a do time, no minimo 1 GiB
	imem=$(( ${5:-512} * 2 )); [ "$imem" -lt 1024 ] && imem=1024

	zipf=$(find "$dir" -maxdepth 1 -type f -name '*.zip' | head -n 1)
	[ -f "$zipf" ] || ia_fail "zip do problema nao encontrado em $dir"
	ia_bin interact "gcc -O2 -o interact interact.c" interact.c
	launcher="$rundir/interact"
	ia_bin interactor "g++ -O2 -std=c++23 -o interactor interactor.cpp" interactor.cpp testlib.h
	inter="$rundir/interactor"
}

# ia_bin NOME "COMANDO" FONTES...: usa run/NOME do pacote (estatico, compilado na importacao); sem
# ele, ou se nao executar nesta maquina, compila das fontes do pacote. Fica em run/ (0700) e vale
# para todos os testes da run.
ia_bin() {
	local n=$1 cmd=$2 f
	shift 2
	[ -x "$rundir/$n" ] && return
	if unzip -p "$zipf" "run/$n" > "$rundir/$n" 2>/dev/null && [ -s "$rundir/$n" ]; then
		chmod 700 "$rundir/$n"
		ia_runs "$rundir/$n" && return
		echo "interactive: run/$n do pacote nao executa nesta maquina, compilando" >&2
	fi
	rm -rf "$rundir/$n" "$rundir/src.$n"
	mkdir -m 700 "$rundir/src.$n" || ia_fail "mkdir src.$n"
	for f in "$@"; do
		unzip -p "$zipf" "run/$f" > "$rundir/src.$n/$f" 2>/dev/null && [ -s "$rundir/src.$n/$f" ] \
			|| ia_fail "pacote sem run/$n e sem run/$f"
	done
	( cd "$rundir/src.$n" && timeout -k 10 180 $cmd ) > "$rundir/src.$n/build.log" 2>&1 \
		|| { head -c 2000 "$rundir/src.$n/build.log"; ia_fail "falha compilando run/$n ($cmd)"; }
	mv "$rundir/src.$n/$n" "$rundir/$n" && chmod 700 "$rundir/$n" || ia_fail "erro instalando run/$n"
}

# ia_run [-Z] -- SOLUCAO...   (SOLUCAO = o safeexec com os limites, SEM -i/-o: o stdin/stdout do
# safeexec, herdados pelo time, sao os pipes do launcher)
ia_run() {
	local z=""
	[ "$1" = "-Z" ] && { z="-Z"; shift; }
	[ "$1" = "--" ] && shift
	# interactor e solucao na MESMA CPU: cada round-trip vira troca de contexto local, sem acordar
	# outra CPU (nos AJs, 1,2-3x mais rapido e com tempo estavel; menos tempo de sistema cobrado do
	# TL do time). ia_pin=auto (padrao: a ultima CPU), um numero, ou vazio para nao fixar.
	local pin=() c=${ia_pin-auto}
	[ "$c" = auto ] && c=$(( $(nproc) - 1 ))
	[ -n "$c" ] && pin=(-a "$c")
	# -w: teto de tudo (backstop; o safeexec ja corta o time em $wall); -g: o interactor tem 5 s
	# para terminar depois da solucao; -c/-m/-f: CPU, memoria e arquivo (tout) do interactor;
	# -k: no fim mata qualquer processo que sobrou do usuario do time
	"$launcher" -S $z "${pin[@]}" -w $((wall + 20)) -g 5 -c $((wall + 5)) -m "$imem" -f 65536 -k "$bocau:$bocag" \
		-e "$ierr" -o "$ires" -- "$inter" "$input" "$tout" "${ans[@]}" -- "$@"
	rc=$?
}

# ia_finish: traduz o resultado do launcher para o contrato do BOCA e sai
#   0..3 (interactor OK/WA/PE/FAIL): exit 0, o compare/<lang> le run/verdict.X
#   10+X (vale o veredito da solucao): exit X, o codigo do safeexec (2/9 RE, 3 TLE, 7 MLE...)
ia_finish() {
	local v msg
	v=$(sed -n 's/^verdict=//p' "$ires" 2>/dev/null)
	msg=$(grep -m1 -v '^[[:space:]]*$' "$ierr" 2>/dev/null | tr -cd '[:print:]' | cut -c1-200)
	{ echo "===== interact:"; cat "$ires" 2>/dev/null; echo "===== interactor stderr:"; head -c 4096 "$ierr" 2>/dev/null; echo; } >&2
	case $rc in
	0|1|2|3)
		printf '%s\n%s\n' "$v" "$msg" > "$verdict"
		[ -f "$tout" ] && cat "$tout"
		exit 0 ;;
	1[0-9])
		printf '%s\n%s\n' "$v" "$msg" > "$verdict"
		echo "interactive: $v (interactor: $msg)"
		exit $((rc - 10)) ;;
	*)
		echo "interactive: erro do launcher (rc=$rc)"
		exit 43 ;;
	esac
}
