from comfyui_restoration.chunking import plan_video_chunks, route_audio


def test_audio_router_covers_timeline_and_marks_speech():
    segments = route_audio(100_000, [(20_000, 30_000)], padding_samples=100, fade_samples=50)
    assert segments[0].end_sample == segments[1].start_sample
    assert segments[1].process is True
    assert segments[-1].end_sample == 100_000


def test_video_chunks_preserve_frame_coverage_with_overlap():
    chunks = plan_video_chunks(500, chunk_frames=200, overlap_frames=10, scene_cuts=[180])
    assert chunks[0].start_frame == 0
    assert chunks[-1].end_frame == 500
    assert all(chunk.process_start <= chunk.start_frame <= chunk.end_frame <= chunk.process_end for chunk in chunks)
