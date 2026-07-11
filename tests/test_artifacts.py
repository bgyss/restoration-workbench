from comfyui_restoration.core import AudioArtifact, VideoArtifact


def test_typed_artifacts_capture_timeline_and_geometry():
    audio = AudioArtifact("audio.wav", 48000, 2, 48000, -21.0)
    video = VideoArtifact("video.mkv", 720, 544, 25, "25/1", dar="4:3")
    assert audio.sample_rate == 48000 and audio.timeline_offset_ms == -21.0
    assert video.width == 720 and video.dar == "4:3"
