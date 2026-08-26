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
from src.analysis.visual import analyse_motion_intensity, analyse_visual_quality
from src.ai.creative_director import (
    generate_creative_review,
    get_ai_service_status,
)
from src.ai.payload import build_creative_review_payload, payload_fingerprint

UPLOAD_DIR = Path("data/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def _render_persisted_scorecard(analysis_result: dict) -> None:
    payload = analysis_result["payload"]
    overall = payload["overall"]

    st.subheader("Creative Scorecard")
    st.caption(
        "This is a transparent heuristic quality score, not a validated "
        "reach or conversion prediction."
    )

    with st.container(horizontal=True):
        st.metric(
            "Overall Creative Score",
            f"{overall['score']} / 100",
            overall["label"],
            border=True,
        )
        st.metric(
            "Campaign Objective Fit",
            f"{payload['objective']['score']} / 100",
            payload["objective"]["objective"],
            border=True,
        )
        st.metric(
            "Technical Quality",
            f"{payload['technical']['score']} / 100",
            payload["technical"]["label"],
            border=True,
        )
        st.metric(
            "Platform Fit",
            f"{payload['platform']['score']} / 100",
            payload["platform"]["target_platform"],
            border=True,
        )
        st.metric(
            "Visual Quality",
            f"{payload['visual']['score']} / 100",
            border=True,
        )


def _render_ai_review(review: dict) -> None:
    st.subheader("Creative Review")
    st.write("**Summary**")
    st.write(review["summary"])

    st.write("**What Works**")
    for strength in review["what_works"]:
        st.write("•", strength)

    st.write("**Priority Improvements**")
    for improvement in review["priority_improvements"]:
        with st.container(border=True):
            st.write(
                f"**{improvement['priority'].title()} priority: "
                f"{improvement['area']}**"
            )
            st.write(improvement["recommendation"])
            st.caption(f"Evidence: {improvement['evidence']}")

    with st.expander("Hook Lab"):
        hook_review = review["hook_review"]
        st.write("**Current hook:**", hook_review["current_hook"] or "Not available")
        st.write(hook_review["assessment"])

        for alternative in hook_review["alternatives"]:
            st.write(
                f"**{alternative['style'].title()}:** "
                f"{alternative['text']}"
            )

    with st.expander("CTA Lab"):
        cta_review = review["cta_review"]
        st.write("**Current CTA:**", cta_review["current_cta"] or "Not detected")
        st.write(cta_review["assessment"])

        for alternative in cta_review["alternatives"]:
            st.write("•", alternative)

    with st.expander("Suggested Video Structure"):
        st.dataframe(
            review["suggested_structure"],
            hide_index=True,
            width="stretch",
        )

    with st.expander("Platform Advice"):
        for advice in review["platform_advice"]:
            st.write("•", advice)

    st.write("**Final Takeaway**")
    st.write(review["final_takeaway"])


def _render_ai_creative_director(analysis_result: dict) -> None:
    payload = analysis_result["payload"]
    fingerprint = payload_fingerprint(payload)
    stored_fingerprint = st.session_state.get("ai_review_payload_hash")

    if stored_fingerprint != fingerprint:
        st.session_state.ai_review_result = None
        st.session_state.ai_review_payload_hash = fingerprint

    st.divider()
    st.subheader("AI Creative Director")
    st.caption(
        "Interprets the deterministic analysis and returns structured, "
        "evidence-based creative recommendations. It does not predict reach, "
        "virality, conversion, or retention."
    )
    service_status = get_ai_service_status()
    last_result = st.session_state.get("ai_review_result")

    st.caption(f"AI provider: {service_status['provider'].title()}")
    st.caption(f"Configured model: {service_status['model']}")

    with st.expander("AI Service Status"):
        st.write(
            "**API key configured:**",
            "Yes" if service_status["api_key_configured"] else "No",
        )
        st.write("**Provider:**", service_status["provider"].title())
        st.write("**Model:**", service_status["model"])

        if last_result:
            st.write(
                "**Last request:**",
                "Success" if last_result["success"] else "Failed",
            )
            st.write(
                "**Error category:**",
                last_result.get("error_category") or "None",
            )
        else:
            st.write("**Last request:** Not run")

    if st.button(
        "Generate AI Creative Review",
        type="secondary",
        width="stretch",
        key="generate_ai_creative_review",
    ):
        with st.spinner("Generating AI Creative Review..."):
            st.session_state.ai_review_result = generate_creative_review(payload)
            st.session_state.ai_review_payload_hash = fingerprint

    ai_result = st.session_state.get("ai_review_result")

    if ai_result:
        if ai_result["success"]:
            _render_ai_review(ai_result["review"])
        else:
            st.warning(ai_result["error"])

st.set_page_config(
    page_title="Creative Intelligence Platform",
    page_icon="🎬",
    layout="wide",
)

st.title("🎬 Creative Intelligence Platform")
st.caption("AI-assisted analysis and optimisation for marketing videos.")
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

st.session_state.setdefault("analysis_result", None)
st.session_state.setdefault("analysis_signature", None)
st.session_state.setdefault("ai_review_result", None)
st.session_state.setdefault("ai_review_payload_hash", None)
st.session_state.setdefault("analysis_displayed_this_run", False)
st.session_state.analysis_displayed_this_run = False

if uploaded_video:
    current_signature = (
        f"{uploaded_video.name}:"
        f"{getattr(uploaded_video, 'size', 0)}:"
        f"{client_name}:"
        f"{campaign_name}:"
        f"{objective}:"
        f"{platform}"
    )

    if st.session_state.analysis_signature != current_signature:
        st.session_state.analysis_result = None
        st.session_state.ai_review_result = None
        st.session_state.ai_review_payload_hash = None
        st.session_state.analysis_signature = current_signature

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
                visual_quality = analyse_visual_quality(keyframes)
                motion_analysis = analyse_motion_intensity(
                    video_path=str(video_path),
                    frame_inputs=keyframes,
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
                    visual_score=visual_quality["score"],
                    hook_score=hook_analysis["score"] if hook_analysis else 0,
                    cta_score=cta_analysis["score"] if cta_analysis else 0,
                    pacing_score=pacing_score["score"],
                )

                recommendations = build_recommendations(
                    creative_score=creative_score,
                    technical_quality=technical_quality,
                    platform_fit=platform_fit,
                    visual_quality=visual_quality,
                    motion_analysis=motion_analysis,
                    hook_analysis=hook_analysis,
                    cta_analysis=cta_analysis,
                    pacing_score=pacing_score,
                    objective_analysis=objective_analysis,
                )

                creative_review_payload = build_creative_review_payload(
                    client_name=client_name,
                    campaign_name=campaign_name,
                    objective=objective,
                    target_platform=platform,
                    video_metadata=analysis,
                    transcript=transcription,
                    speech_analysis=speech_analysis,
                    hook_analysis=hook_analysis,
                    cta_analysis=cta_analysis,
                    message_analysis=message_analysis,
                    story_analysis=story_analysis,
                    scene_analysis=scene_analysis,
                    pacing_analysis=pacing_analysis,
                    visual_quality=visual_quality,
                    motion_analysis=motion_analysis,
                    technical_quality=technical_quality,
                    platform_fit=platform_fit,
                    objective_analysis=objective_analysis,
                    creative_score=creative_score,
                    recommendations=recommendations,
                )

                st.session_state.analysis_result = {
                    "payload": creative_review_payload,
                    "signature": current_signature,
                }
                st.session_state.ai_review_result = None
                st.session_state.ai_review_payload_hash = None
                st.session_state.analysis_displayed_this_run = True

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
                    st.metric(
                        "Visual Quality",
                        f"{visual_quality['score']} / 100",
                        visual_quality["label"],
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

                    st.write("**Visual quality reasons**")
                    visual_components = {
                        "sharpness": visual_quality["sharpness_score"],
                        "exposure": visual_quality["exposure_score"],
                        "contrast": visual_quality["contrast_score"],
                        "visual_consistency": visual_quality["consistency_score"],
                    }
                    for component, score in visual_components.items():
                        st.write(
                            f"{component.replace('_', ' ').title()}: {score} / 100"
                        )

                    for reason in visual_quality["reasons"]:
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

                st.subheader("Visual Intelligence")

                with st.container(horizontal=True):
                    st.metric(
                        "Visual Quality Score",
                        f"{visual_quality['score']} / 100",
                        visual_quality["label"],
                        border=True,
                    )
                    st.metric(
                        "Sharpness",
                        f"{visual_quality['sharpness_score']} / 100",
                        border=True,
                    )
                    st.metric(
                        "Exposure",
                        f"{visual_quality['exposure_score']} / 100",
                        border=True,
                    )
                    st.metric(
                        "Contrast",
                        f"{visual_quality['contrast_score']} / 100",
                        border=True,
                    )
                    st.metric(
                        "Visual Consistency",
                        f"{visual_quality['consistency_score']} / 100",
                        border=True,
                    )

                st.write(
                    "**Visual Activity / Motion Level:**",
                    motion_analysis["motion_level"],
                )

                st.caption(
                    f"Average frame difference: "
                    f"{motion_analysis['average_frame_difference']}"
                )

                if visual_quality["warnings"] or motion_analysis["warnings"]:
                    st.write("**Warnings:**")

                    for warning in (
                        visual_quality["warnings"]
                        + motion_analysis["warnings"]
                    ):
                        st.warning(warning)
                else:
                    st.success("No major visual quality warnings detected.")

                visual_recommendations = [
                    item for item in recommendations
                    if item["area"].startswith("Visual")
                ]

                if visual_recommendations:
                    st.write("**Visual improvement recommendations:**")

                    for item in visual_recommendations:
                        st.write(
                            f"**{item['priority']} priority: "
                            f"{item['area']}**"
                        )
                        st.write(item["recommendation"])
                else:
                    st.write(
                        "Visual quality is strong and consistent."
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

                _render_ai_creative_director(
                    st.session_state.analysis_result
                )

            except Exception as error:
                st.error(f"Video analysis failed: {error}")

    if (
        st.session_state.analysis_result
        and not st.session_state.analysis_displayed_this_run
    ):
        _render_persisted_scorecard(
            st.session_state.analysis_result
        )
        _render_ai_creative_director(
            st.session_state.analysis_result
        )
