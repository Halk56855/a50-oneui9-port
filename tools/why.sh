f=/media/gord/C887-5F91/bootlog.txt; ls -l --time-style=+%H:%M "$f"
for p in 'Error preloading' 'boot_progress_system_run' 'FATAL EXCEPTION IN SYSTEM PROCESS' 'Required services extension' 'boot_progress_ams_ready' 'Start proc .*systemui' 'Fatal signal'; do echo "$(grep -ac "$p" "$f") x  $p"; done
echo "--- last system_server crash:"; grep -a -A2 'FATAL EXCEPTION IN SYSTEM PROCESS' "$f" | grep -a AndroidRuntime | tail -2 | sed -E 's/^.*AndroidRuntime: //' | cut -c1-220
echo "--- last zygote error:"; grep -aE 'E Zygote|failed initialization' "$f" | tail -2 | cut -c19-220
echo "--- last native crash:"; grep -aE 'Fatal signal' "$f" | tail -2 | cut -c19-200
