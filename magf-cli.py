#!/usr/bin/env python3

import argparse
import os
import json
import struct
import tempfile
import ffmpeg
import imageio
from pydub import AudioSegment

MAGIC = b"MAGF\x01\x00"

def normalize_audio(input_audio, output_audio):
    audio = AudioSegment.from_file(input_audio)
    audio = audio.normalize()
    audio.export(output_audio, format="flac")

def encode_magf(images_dir, audio_file, text_file, output_file,
                fps=15, loop=0, title="MAGF Demo", creator="MAGF CLI"):
    with tempfile.TemporaryDirectory() as tmp:
        video_path = os.path.join(tmp, "video.mkv")
        audio_path = None

        # Audio
        if audio_file:
            audio_path = os.path.join(tmp, "audio.flac")
            normalize_audio(audio_file, audio_path)

        # Image sequence → AV1
        (
            ffmpeg
            .input(os.path.join(images_dir, "frame_%03d.png"), framerate=fps)
            .output(
                video_path,
                vcodec="libaom-av1",
                pix_fmt="yuva420p",
                crf=30,
                cpu_used=6,
                g=fps,
                auto_alt_ref=0
            )
            .overwrite_output()
            .run(quiet=True)
        )

        # Mux everything
        inputs = [ffmpeg.input(video_path)]
        if audio_path:
            inputs.append(ffmpeg.input(audio_path))
        if text_file:
            inputs.append(ffmpeg.input(text_file))

        (
            ffmpeg
            .output(
                *inputs,
                output_file,
                c_v="copy",
                c_a="flac",
                c_s="srt",
                shortest=None
            )
            .overwrite_output()
            .run(quiet=True)
        )

        append_magf_header(
            output_file,
            fps=fps,
            loop=loop,
            title=title,
            creator=creator
        )

def append_magf_header(file_path, fps, loop, title, creator):
    duration = probe_duration(file_path)

    header = struct.pack(
        "<6sHfHH",
        MAGIC,
        1,              # version
        duration,       # seconds
        loop,           # loop count (0 = infinite)
        fps
    )

    metadata = {
        "title": title,
        "creator": creator,
        "mime": "video/x-magf"
    }

    with open(file_path, "ab") as f:
        f.write(header)
        f.write(json.dumps(metadata).encode("utf-8"))

def probe_duration(path):
    probe = ffmpeg.probe(path)
    return float(probe["format"]["duration"])

def decode_magf(input_file, extract_frames=False, extract_audio=False):
    if extract_frames:
        (
            ffmpeg
            .input(input_file)
            .output("frame_%03d.png")
            .overwrite_output()
            .run()
        )

    if extract_audio:
        (
            ffmpeg
            .input(input_file)
            .output("audio.flac")
            .overwrite_output()
            .run()
        )

def main():
    parser = argparse.ArgumentParser("MAGF CLI")
    sub = parser.add_subparsers(dest="cmd")

    enc = sub.add_parser("encode")
    enc.add_argument("--images", required=True)
    enc.add_argument("--audio")
    enc.add_argument("--text")
    enc.add_argument("--output", required=True)
    enc.add_argument("--fps", type=int, default=15)
    enc.add_argument("--loop", type=int, default=0)

    dec = sub.add_parser("decode")
    dec.add_argument("input")
    dec.add_argument("--extract-frames", action="store_true")
    dec.add_argument("--extract-audio", action="store_true")

    args = parser.parse_args()

    if args.cmd == "encode":
        encode_magf(
            args.images,
            args.audio,
            args.text,
            args.output,
            args.fps,
            args.loop
        )
    elif args.cmd == "decode":
        decode_magf(
            args.input,
            args.extract_frames,
            args.extract_audio
        )

if __name__ == "__main__":
    main()
