from pathlib import Path
import streamlit as st

from src.video.processor import analyse_video
from src.video.scene_detector import detect_scenes
from src.analysis.pacing import analyse_pacing
from src.video.frame_extractor import extract_keyframes
from src.audio.extractor import extract_audio
from src.audio.transcription import transcribe_audio
from src.analysis.hook import analyse_hook
from src.analysis.cta import analyse_cta
from src.analysis.speech import analyse_speech
from src.analysis.message import analyse_message
from src.analysis.story import analyse_story
from src.analysis.objective import calculate_objective_score
from src.analysis.technical import score_technical_quality
from src.analysis.platform import score_all_platforms, score_platform_fit
from src.analysis.scoring import (
    calculate_creative_score,
    score_pacing_for_creative,
)
from src.analysis.recommendations import build_recommendations

UPLOAD_DIR = Path("data/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

st.set_page_config(
    page_title="ReCreate Creative Intelligence",
    page_icon="🎬",
    layout="wide",
)

st.title("🎬 ReCreate Creative Intelligence")
st.caption("AI-assisted creative quality analysis for marketing videos.")
st.divider()

client_name = st.text_input(
    "Client",
    placeholder="Example: ReCreate Australia",
)

campaign_name = st.text_input(
    "Campaign",
    placeholder="Example: Spring Brand Campaign",
)

objective = st.selectbox(
    "Campaign objective",
    [
        "Brand Awareness",
        "Engagement",
        "Lead Generation",
        "Sales / Conversion",
        "Community Building",
        "Event Promotion",
        "Recruitment",
        "Trust / Authority",
    ],
)

platform = st.selectbox(
    "Target platform",
    [
        "Instagram Reels",
        "TikTok",
        "YouTube Shorts",
        "LinkedIn",
        "Facebook",
        "Website",
        "Other",
    ],
)

uploaded_video = st.file_uploader(
    "Upload marketing video",
    type=["mp4", "mov", "avi", "mkv"],
)

if uploaded_video:
    video_path = UPLOAD_DIR / uploaded_video.name

    with open(video_path, "wb") as file:
        file.write(uploaded_video.getbuffer())

    st.success("Video uploaded successfully.")
    st.video(str(video_path))

    st.subheader("Campaign Information")
    col1, col2 = st.columns(2)

    with col1:
        st.write("**Client:**", client_name or "Not specified")
        st.write("**Objective:**", objective)

    with col2:
        st.write("**Campaign:**", campaign_name or "Not specified")
        st.write("**Platform:**", platform)

    st.divider()

    if st.button(
        "Analyse Video",
        type="primary",
        width="stretch",
    ):

        with st.spinner("Analysing video..."):
            try:
                analysis = analyse_video(str(video_path))
                scene_analysis = detect_scenes(
                    str(video_path)
                )

                pacing_analysis = analyse_pacing(
                    duration=analysis["duration"],
                    scene_count=scene_analysis["scene_count"]
                )
                keyframes = extract_keyframes(
                    str(video_path),
                    "data/frames",
                    frame_count=5
                )
                audio_analysis = extract_audio(
                    str(video_path),
                    "data/audio"
                )
                transcription = None
                technical_quality = score_technical_quality(analysis)
                platform_scores = score_all_platforms(analysis)
                platform_fit = (
                    score_platform_fit(analysis, platform)
                    if platform == "Other"
                    else platform_scores[platform]
                )
                pacing_score = score_pacing_for_creative(pacing_analysis)
                hook_analysis = None
                cta_analysis = None
                speech_analysis = None
                message_analysis = None
                story_analysis = None

                if audio_analysis["has_audio"]:
                    transcription = transcribe_audio(
                        audio_analysis["audio_path"]
                    )

                creative_analysis = None

                if (
                    transcription
                    and transcription["success"]
                    and transcription["words"]
                ):
                    hook_analysis = analyse_hook(
                        transcription["words"]
                    )

                    cta_analysis = analyse_cta(
                        transcription["words"],
                        analysis["duration"]
                    )

                    speech_analysis = analyse_speech(
                        transcription["words"],
                        analysis["duration"]
                    )
                    message_analysis = analyse_message(
                        transcription["transcript"]
                    )

                    story_analysis = analyse_story(
                        hook_analysis,
                        message_analysis,
                        cta_analysis
                    )

                    objective_analysis = calculate_objective_score(
                        objective=objective,
                        hook_score=hook_analysis["score"],
                        message_score=message_analysis["score"],
                        cta_score=cta_analysis["score"],
                        story_score=story_analysis["score"],
                    )

                    creative_analysis = {
                        "hook": hook_analysis,
                        "cta": cta_analysis,
                        "speech": speech_analysis,
                        "message": message_analysis,
                        "story": story_analysis,
                        "objective": objective_analysis,
                    }

                else:
                    objective_analysis = calculate_objective_score(
                        objective=objective,
                        hook_score=0,
                        message_score=0,
                        cta_score=0,
                        story_score=0,
                    )

                creative_score = calculate_creative_score(
                    objective_score=objective_analysis["score"],
                    technical_score=technical_quality["score"],
                    platform_score=platform_fit["score"],
                    hook_score=hook_analysis["score"] if hook_analysis else 0,
                    cta_score=cta_analysis["score"] if cta_analysis else 0,
                    pacing_score=pacing_score["score"],
                )

                recommendations = build_recommendations(
                    creative_score=creative_score,
                    technical_quality=technical_quality,
                    platform_fit=platform_fit,
                    hook_analysis=hook_analysis,
                    cta_analysis=cta_analysis,
                    pacing_score=pacing_score,
                    objective_analysis=objective_analysis,
                )

                st.success("Video analysis complete.")

                st.subheader("Creative Scorecard")

                st.caption(creative_score["disclaimer"])

                with st.container(horizontal=True):
                    st.metric(
                        "Overall Creative Score",
                        f"{creative_score['score']} / 100",
                        creative_score["label"],
                        border=True,
                    )
                    st.metric(
                        "Campaign Objective Fit",
                        f"{objective_analysis['score']} / 100",
                        objective_analysis["objective"],
                        border=True,
                    )
                    st.metric(
                        "Technical Quality",
                        f"{technical_quality['score']} / 100",
                        technical_quality["label"],
                        border=True,
                    )
                    st.metric(
                        "Platform Fit",
                        f"{platform_fit['score']} / 100",
                        platform_fit["platform"],
                        border=True,
                    )

                st.write("**Creative Score weights:**")
                weights_text = ", ".join(
                    f"{name.replace('_', ' ').title()}: {weight * 100:.0f}%"
                    for name, weight in creative_score["weights"].items()
                )
                st.caption(weights_text)

                with st.expander("View component scores and score reasons"):
                    st.write("**Overall component scores**")
                    for component, score in creative_score["components"].items():
                        st.write(
                            f"{component.replace('_', ' ').title()}: {score} / 100"
                        )

                    st.write("**Technical quality reasons**")
                    for component, score in technical_quality["components"].items():
                        st.write(
                            f"{component.replace('_', ' ').title()}: {score} / 100"
                        )

                    for reason in technical_quality["reasons"]:
                        st.write("•", reason)

                    st.write("**Platform fit reasons**")
                    for component, score in platform_fit["components"].items():
                        st.write(
                            f"{component.replace('_', ' ').title()}: {score} / 100"
                        )

                    for reason in platform_fit["reasons"]:
                        st.write("•", reason)

                    st.write("**Pacing score reason**")
                    for reason in pacing_score["reasons"]:
                        st.write("•", reason)

                st.subheader("Recommended Improvements")

                for item in recommendations:
                    with st.container(border=True):
                        st.write(
                            f"**{item['priority']} priority: {item['area']}**"
                        )
                        st.write(item["recommendation"])

                with st.expander("Compare platform compatibility"):
                    for platform_name, platform_result in platform_scores.items():
                        st.write(
                            f"**{platform_name}:** "
                            f"{platform_result['score']} / 100 "
                            f"({platform_result['label']})"
                        )

                st.subheader("Video Intelligence")

                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    st.metric(
                        "Duration",
                        f"{analysis['duration']} sec"
                    )

                with col2:
                    st.metric(
                        "Frame Rate",
                        f"{analysis['fps']} FPS"
                    )

                with col3:
                    st.metric(
                        "Resolution",
                        analysis["resolution"]
                    )

                with col4:
                    st.metric(
                        "File Size",
                        f"{analysis['file_size_mb']} MB"
                    )

                st.divider()

                col1, col2, col3 = st.columns(3)

                with col1:
                    st.write(
                        "**Orientation:**",
                        analysis["orientation"]
                    )

                with col2:
                    st.write(
                        "**Aspect Ratio:**",
                        analysis["aspect_ratio"]
                    )

                with col3:
                    st.write(
                        "**Frame Count:**",
                        analysis["frame_count"]
                    )
                st.divider()

                st.subheader("Scene & Pacing Analysis")

                col1, col2, col3 = st.columns(3)

                with col1:
                    st.metric(
                        "Detected Scenes",
                        scene_analysis["scene_count"]
                    )

                with col2:
                    st.metric(
                        "Average Scene Duration",
                        f"{pacing_analysis['average_scene_duration']} sec"
                    )

                with col3:
                    st.metric(
                        "Pacing",
                        pacing_analysis["pacing_label"]
                    )

                st.write(
                    "**Scenes Per Minute:**",
                    pacing_analysis["scenes_per_minute"]
                )

                if scene_analysis["scene_changes"]:
                    st.write("**Detected scene changes:**")

                    scene_times = ", ".join(
                        f"{time}s"
                        for time in scene_analysis["scene_changes"]
                    )

                    st.write(scene_times)
                else:
                    st.write(
                        "No major scene transitions detected."
                    )
                st.divider()

                st.subheader("Visual Keyframes")

                st.caption(
                    "Representative frames sampled throughout the video."
                )

                if keyframes:

                    columns = st.columns(len(keyframes))

                    for column, frame in zip(columns, keyframes):

                        with column:

                            st.image(
                                frame["path"],
                                width="stretch"
                            )

                            st.caption(
                                f"{frame['timestamp']} sec"
                            )

                else:
                    st.warning(
                        "No keyframes could be extracted."
                    )

                st.divider()

                st.subheader("Audio Analysis")

                if audio_analysis["has_audio"]:

                    st.success("Audio track detected.")

                    st.write(
                        "**Extracted audio file:**",
                        audio_analysis["audio_path"]
                    )

                else:

                    st.warning(
                        "No usable audio track was detected."
                    )

                    if audio_analysis.get("error"):
                        st.caption(
                            f"Details: {audio_analysis['error']}"
                        )
                if audio_analysis["has_audio"]:

                    st.divider()
                    st.subheader("Speech Transcription")

                    if transcription and transcription["success"]:

                        st.success("Transcription complete.")

                        st.write("**Transcript:**")
                        st.write(
                            transcription["transcript"]
                            or "No speech was detected."
                        )

                        if transcription["confidence"] is not None:
                            st.write(
                                "**Confidence:**",
                                f"{transcription['confidence'] * 100:.2f}%"
                            )

                        if transcription["words"]:

                            with st.expander("View word timestamps"):

                                for word in transcription["words"]:
                                    st.write(
                                        f"{word['start']:.2f}s – "
                                        f"{word['end']:.2f}s | "
                                        f"{word['word']}"
                                    )

                    elif transcription:

                        st.error(
                            f"Transcription failed: {transcription['error']}"
                        )

                if creative_analysis:

                    st.divider()
                    st.subheader("Creative Intelligence")

                    st.caption(
                        "Initial heuristic analysis based on transcript timing "
                        "and recognised marketing structures."
                    )

                    hook = creative_analysis["hook"]
                    cta = creative_analysis["cta"]
                    speech = creative_analysis["speech"]

                    col1, col2, col3 = st.columns(3)

                    with col1:
                        st.metric(
                            "Hook Score",
                            f"{hook['score']} / 100"
                        )

                    with col2:
                        st.metric(
                            "CTA Score",
                            f"{cta['score']} / 100"
                        )

                    with col3:
                        st.metric(
                            "Speech Rate",
                            f"{speech['words_per_minute']} WPM"
                        )

                    st.subheader("Hook Analysis")

                    st.write(
                        "**Opening:**",
                        hook["hook_text"]
                        or "No opening hook detected."
                    )

                    st.write(
                        "**Hook Type:**",
                        hook["hook_type"]
                    )

                    if hook["hook_start"] is not None:
                        st.write(
                            "**Hook Timing:**",
                            f"{hook['hook_start']}s – "
                            f"{hook['hook_end']}s"
                        )

                    for reason in hook["reasons"]:
                        st.write("•", reason)

                    st.subheader("Call to Action")

                    if cta["cta_detected"]:
                        st.success("CTA detected.")

                        st.write(
                            "**CTA excerpt:**",
                            cta["cta_text"]
                        )

                        st.write(
                            "**CTA starts at:**",
                            f"{cta['cta_start']} sec"
                        )

                        st.write(
                            "**CTA position:**",
                            cta["cta_position"]
                        )

                    else:
                        st.warning(
                            "No clear spoken call to action detected."
                        )

                    st.subheader("Speech Analysis")

                    st.write(
                        "**Word Count:**",
                        speech["word_count"]
                    )

                    st.write(
                        "**Speech Rate:**",
                        speech["speech_rate"]
                    )

                    message = creative_analysis["message"]
                    story = creative_analysis["story"]
                    objective_result = creative_analysis["objective"]

                    st.divider()

                    st.subheader("Message Clarity")

                    st.metric(
                        "Message Clarity Score",
                        f"{message['score']} / 100"
                    )

                    st.write(
                        "**Clarity:**",
                        message["clarity_label"]
                    )

                    for reason in message["reasons"]:
                        st.write("•", reason)


                    st.subheader("Story Structure")

                    st.metric(
                        "Story Structure Score",
                        f"{story['score']} / 100"
                    )

                    st.write(
                        "**Structure:**",
                        story["label"]
                    )

                    for component, present in story["components"].items():
                        st.write(
                            f"{'✅' if present else '❌'} "
                            f"{component.title()}"
                        )


                    st.subheader("Campaign Objective Score")

                    st.metric(
                        f"{objective_result['objective']} Score",
                        f"{objective_result['score']} / 100"
                    )

                    st.caption(
                        "This score changes according to the selected campaign objective."
                    )


            except Exception as error:
                st.error(f"Video analysis failed: {error}")
