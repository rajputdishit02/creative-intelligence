from pathlib import Path
import streamlit as st

from src.video.processor import analyse_video
from src.video.scene_detector import detect_scenes
from src.analysis.pacing import analyse_pacing
from src.video.frame_extractor import extract_keyframes

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
        use_container_width=True,
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

                st.success("Video analysis complete.")

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
                                use_container_width=True
                            )

                            st.caption(
                                f"{frame['timestamp']} sec"
                            )

                else:
                    st.warning(
                        "No keyframes could be extracted."
                    )
            except Exception as error:
                st.error(f"Video analysis failed: {error}")
