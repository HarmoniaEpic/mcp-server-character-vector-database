"""
Gradio theme configuration
"""

import gradio as gr


def get_monitor_theme():
    """モニター用のカスタムテーマを取得"""
    return gr.themes.Soft(
        primary_hue="purple",
        secondary_hue="blue",
        neutral_hue="gray",
        spacing_size="md",
        radius_size="md",
        font=[gr.themes.GoogleFont("Noto Sans JP"), "sans-serif"]
    ).set(
        body_background_fill="*neutral_50",
        body_background_fill_dark="*neutral_950",
        block_background_fill="white",
        block_background_fill_dark="*neutral_900",
        block_border_color="*primary_200",
        block_border_color_dark="*primary_700",
        block_label_background_fill="*primary_100",
        block_label_background_fill_dark="*primary_800",
        block_label_text_color="*primary_900",
        block_label_text_color_dark="*primary_100",
        block_title_text_color="*primary_900",
        block_title_text_color_dark="*primary_100",
        input_background_fill="white",
        input_background_fill_dark="*neutral_800",
        input_border_color="*neutral_300",
        input_border_color_dark="*neutral_600",
        input_border_color_focus="*primary_500",
        input_border_color_focus_dark="*primary_400",
        button_primary_background_fill="*primary_600",
        button_primary_background_fill_hover="*primary_700",
        button_primary_background_fill_dark="*primary_500",
        button_primary_background_fill_hover_dark="*primary_400",
    )
