# AI 노래 업로드 (Suno → YouTube)

사용자가 Suno mp3를 주고 "업로드해줘"라고 하면:
1. 메타데이터(ffprobe format_tags)에서 제목과 `lyrics-eng` 가사를 읽는다.
2. spec.json 작성 → `python3 music/make.py spec.json OUTDIR` (풀버전 1920x1080 + 34초 하이라이트 쇼츠 + 썸네일 + 표지)
   - 표지 문구(small/big), palette, genre는 곡 분위기에 맞게 정한다. 하이라이트 구간은 자동(가장 뜨거운 후렴).
3. thumb.png와 short.png를 확인해 글자 넘침이 없는지 본다.
4. full.mp4, short.mp4, thumb.png를 videos/ 에 올려 push → raw.githubusercontent.com URL이 200인지 확인.
5. Metricool(blogId 7746989, Asia/Seoul) **예약 없이 바로 게시**: 날짜는 지금 시각 + 2~3분.
   - 풀버전: youtubeData type "video", category MUSIC, videoThumbnailUrl=thumb, isAiGeneratedContent true
   - 쇼츠: 풀버전 5분 뒤, type "short", 제목에 #shorts
   - 둘 다 설명란에 "AI(Suno)로 만든 오리지널 노래" 명시, madeForKids false, public
6. 응답의 media가 static.metricool.com으로 바뀐 것 확인 후 videos/ 파일 삭제 push.
