cd C:/project/trend/research/work/yt
for id in "$@"; do
  if [ ! -f "$id.json" ]; then
    yt-dlp --no-update --sleep-requests 1 --dump-json --no-download "https://www.youtube.com/watch?v=$id" > "$id.json" 2>"$id.meta.log" || echo "$id meta FAIL: $(tail -1 "$id.meta.log")"
  fi
  if [ ! -f "$id.ko.vtt" ]; then
    yt-dlp --no-update --sleep-requests 1 --sleep-subtitles 2 --write-sub --write-auto-sub --sub-lang "ko" --sub-format vtt --skip-download -o "%(id)s" "https://www.youtube.com/watch?v=$id" >"$id.log" 2>&1
    echo "$id sub rc=$? $(grep -c . "$id.ko.vtt" 2>/dev/null) lines"
  else
    echo "$id sub ok"
  fi
done
echo DONE
