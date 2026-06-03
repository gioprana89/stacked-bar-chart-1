import streamlit as st
import pandas as pd
import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from io import BytesIO


# =========================================================
# Page configuration
# =========================================================


st.set_page_config(
    page_title="Two-Panel Time Series Visualization",
    page_icon="📈",
    layout="wide"
)

st.markdown(
    """
    ### Developed by Prana Ugiana Gio

    **Website:** [pranaugi.com](https://pranaugi.com/)

    **YouTube:** [STATKOMAT](https://www.youtube.com/@STATKOMAT)

    **Online Store:** [lynk.id/statkomat](https://lynk.id/statkomat)

    **Training Data for This Application:**  
    [Download training data from Google Drive](https://drive.google.com/drive/folders/1iSadK2HPOtB90a-JE5QVnJPolnuIzqzV?usp=sharing)

    ---
    """
)



# =========================================================
# Color palettes
# =========================================================
COLOR_PALETTES = {
    "Navy - Dark Red": {
        "Panel A": "#000080",   # navy
        "Panel B": "#8B0000"    # darkred
    },
    "Scopus Orange - Blue": {
        "Panel A": "#E97132",
        "Panel B": "#1F77B4"
    },
    "Academic Blue - Green": {
        "Panel A": "#1F4E79",
        "Panel B": "#548235"
    },
    "Black - Gray": {
        "Panel A": "#000000",   # black
        "Panel B": "#696969"    # dimgray
    },
    "Purple - Orange": {
        "Panel A": "#7030A0",
        "Panel B": "#C55A11"
    }
}


# =========================================================
# Helper functions
# =========================================================
@st.cache_data
def read_uploaded_file(uploaded_file):
    file_name = uploaded_file.name.lower()

    if file_name.endswith(".csv"):
        return pd.read_csv(uploaded_file)

    if file_name.endswith((".xlsx", ".xls")):
        return pd.read_excel(uploaded_file)

    raise ValueError("Format file tidak didukung. Gunakan CSV, XLSX, atau XLS.")


def make_sample_data():
    dates = pd.date_range("2022-01-01", periods=36, freq="M")

    close = [
        101, 103, 105, 102, 108, 111, 115, 117, 116, 120, 123, 125,
        121, 119, 124, 128, 130, 133, 136, 134, 138, 141, 144, 147,
        145, 148, 151, 155, 157, 160, 158, 162, 165, 168, 171, 175
    ]

    df = pd.DataFrame({
        "Date": dates,
        "Close": close
    })

    df["Daily Stock Return (%)"] = df["Close"].pct_change() * 100
    df["Daily Stock Return (%)"] = df["Daily Stock Return (%)"].fillna(0)

    return df


def convert_to_datetime(series):
    """
    Mengubah kolom menjadi datetime.
    Bisa membaca:
    - format tanggal biasa: 2024-01-01
    - format bulan/tahun
    - format tahun saja: 2024
    """

    # Jika kolom numerik dan terlihat seperti tahun
    if pd.api.types.is_numeric_dtype(series):
        sample = series.dropna()

        if not sample.empty:
            year_like_ratio = sample.between(1800, 2200).mean()

            if year_like_ratio > 0.8:
                return pd.to_datetime(
                    series.astype("Int64").astype(str),
                    format="%Y",
                    errors="coerce"
                )

    return pd.to_datetime(series, errors="coerce")


def apply_publication_style(font_family, base_font_size):
    plt.rcParams["font.family"] = font_family
    plt.rcParams["font.size"] = base_font_size
    plt.rcParams["axes.labelsize"] = base_font_size + 1
    plt.rcParams["axes.titlesize"] = base_font_size + 2
    plt.rcParams["legend.fontsize"] = base_font_size - 1
    plt.rcParams["xtick.labelsize"] = base_font_size - 1
    plt.rcParams["ytick.labelsize"] = base_font_size - 1
    plt.rcParams["figure.dpi"] = 100


def create_two_panel_chart(
    df,
    date_col,
    panel_a_col,
    panel_b_col,
    panel_a_color,
    panel_b_color,
    overall_title,
    panel_a_title,
    panel_b_title,
    panel_a_ylabel,
    panel_b_ylabel,
    x_label,
    figsize_width,
    figsize_height,
    line_width,
    marker_size,
    show_marker,
    show_grid,
    date_format,
    rotate_xticks,
    font_family,
    base_font_size
):
    apply_publication_style(font_family, base_font_size)

    fig, axes = plt.subplots(
        nrows=2,
        ncols=1,
        figsize=(figsize_width, figsize_height),
        sharex=True
    )

    marker_style = "o" if show_marker else None

    # -----------------------------
    # Panel A
    # -----------------------------
    axes[0].plot(
        df[date_col],
        df[panel_a_col],
        color=panel_a_color,
        linestyle="-",
        linewidth=line_width,
        marker=marker_style,
        markersize=marker_size,
        label=panel_a_col
    )

    axes[0].set_title(panel_a_title)
    axes[0].set_ylabel(panel_a_ylabel)

    if show_grid:
        axes[0].grid(True, linestyle="--", linewidth=0.6, alpha=0.7)

    axes[0].legend(loc="upper left", frameon=True)

    # -----------------------------
    # Panel B
    # -----------------------------
    axes[1].plot(
        df[date_col],
        df[panel_b_col],
        color=panel_b_color,
        linestyle="-",
        linewidth=line_width,
        marker=marker_style,
        markersize=marker_size,
        label=panel_b_col
    )

    axes[1].set_title(panel_b_title)
    axes[1].set_xlabel(x_label)
    axes[1].set_ylabel(panel_b_ylabel)

    if show_grid:
        axes[1].grid(True, linestyle="--", linewidth=0.6, alpha=0.7)

    axes[1].legend(loc="upper left", frameon=True)

    # -----------------------------
    # X-axis formatting
    # -----------------------------
    axes[1].xaxis.set_major_locator(mdates.AutoDateLocator())
    axes[1].xaxis.set_major_formatter(mdates.DateFormatter(date_format))

    plt.setp(
        axes[1].get_xticklabels(),
        rotation=rotate_xticks,
        ha="right"
    )

    # -----------------------------
    # Overall title
    # -----------------------------
    fig.suptitle(
        overall_title,
        fontsize=base_font_size + 3,
        fontweight="bold",
        y=0.98
    )

    plt.tight_layout(rect=[0, 0, 1, 0.96])

    return fig


def fig_to_png_bytes(fig, dpi):
    buffer = BytesIO()

    fig.savefig(
        buffer,
        dpi=dpi,
        format="png",
        bbox_inches="tight"
    )

    buffer.seek(0)
    return buffer


# =========================================================
# App title
# =========================================================
st.title("📈 Two-Panel Publication-Style Time Series")
st.caption(
    "Aplikasi Streamlit untuk membuat grafik time series dua panel seperti visualisasi artikel/jurnal."
)


# =========================================================
# Sidebar: Upload data
# =========================================================
with st.sidebar:
    st.header("1. Upload Data")

    uploaded_file = st.file_uploader(
        "Upload file CSV atau Excel",
        type=["csv", "xlsx", "xls"]
    )

    use_sample_data = st.checkbox(
        "Gunakan data contoh",
        value=True if uploaded_file is None else False
    )


# =========================================================
# Load data
# =========================================================
try:
    if uploaded_file is not None:
        df = read_uploaded_file(uploaded_file)
    elif use_sample_data:
        df = make_sample_data()
    else:
        st.info("Silakan upload data atau aktifkan data contoh.")
        st.stop()

except Exception as e:
    st.error(f"Gagal membaca data: {e}")
    st.stop()


# =========================================================
# Data preview
# =========================================================
st.subheader("Preview Data")
st.dataframe(df.head(20), use_container_width=True)


# =========================================================
# Column selection
# =========================================================
columns = df.columns.tolist()

date_candidates = [
    col for col in columns
    if "date" in col.lower()
    or "tanggal" in col.lower()
    or "time" in col.lower()
    or "year" in col.lower()
    or "tahun" in col.lower()
]

default_date_col = date_candidates[0] if date_candidates else columns[0]

numeric_columns = [
    col for col in columns
    if pd.to_numeric(df[col], errors="coerce").notna().sum() > 0
]

if len(numeric_columns) < 2:
    st.error("Data harus memiliki minimal dua kolom numerik untuk Panel A dan Panel B.")
    st.stop()


with st.sidebar:
    st.header("2. Pilih Kolom")

    date_col = st.selectbox(
        "Kolom tanggal",
        columns,
        index=columns.index(default_date_col)
    )

    default_panel_a = "Close" if "Close" in numeric_columns else numeric_columns[0]

    default_panel_b = (
        "Daily Stock Return (%)"
        if "Daily Stock Return (%)" in numeric_columns
        else numeric_columns[1]
    )

    panel_a_col = st.selectbox(
        "Kolom Panel A",
        numeric_columns,
        index=numeric_columns.index(default_panel_a)
    )

    panel_b_col = st.selectbox(
        "Kolom Panel B",
        numeric_columns,
        index=numeric_columns.index(default_panel_b)
    )


# =========================================================
# Prepare selected data
# =========================================================
working_df = df[[date_col, panel_a_col, panel_b_col]].copy()

working_df[date_col] = convert_to_datetime(working_df[date_col])
working_df[panel_a_col] = pd.to_numeric(working_df[panel_a_col], errors="coerce")
working_df[panel_b_col] = pd.to_numeric(working_df[panel_b_col], errors="coerce")

working_df = working_df.dropna(subset=[date_col, panel_a_col, panel_b_col])
working_df = working_df.sort_values(date_col)

if working_df.empty:
    st.error("Data tidak valid setelah kolom tanggal dan numerik diproses.")
    st.stop()


# =========================================================
# Sidebar: Time range
# =========================================================
min_date = working_df[date_col].min().date()
max_date = working_df[date_col].max().date()

with st.sidebar:
    st.header("3. Range Waktu")

    selected_range = st.date_input(
        "Pilih range tanggal",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )

    if isinstance(selected_range, tuple) and len(selected_range) == 2:
        start_date, end_date = selected_range
    else:
        start_date, end_date = min_date, max_date


filtered_df = working_df[
    (working_df[date_col] >= pd.to_datetime(start_date))
    & (working_df[date_col] <= pd.to_datetime(end_date))
].copy()

if filtered_df.empty:
    st.warning("Tidak ada data pada range waktu yang dipilih.")
    st.stop()


# =========================================================
# Sidebar: Chart style
# =========================================================
with st.sidebar:
    st.header("4. Gaya Grafik")

    color_palette = st.selectbox(
        "Variasi warna",
        list(COLOR_PALETTES.keys())
    )

    default_panel_a_color = COLOR_PALETTES[color_palette]["Panel A"]
    default_panel_b_color = COLOR_PALETTES[color_palette]["Panel B"]

    panel_a_color = st.color_picker(
        "Warna Panel A",
        default_panel_a_color
    )

    panel_b_color = st.color_picker(
        "Warna Panel B",
        default_panel_b_color
    )

    show_marker = st.checkbox("Tampilkan marker titik", value=True)
    show_grid = st.checkbox("Tampilkan grid", value=True)

    line_width = st.slider(
        "Ketebalan garis",
        min_value=0.5,
        max_value=5.0,
        value=1.8,
        step=0.1
    )

    marker_size = st.slider(
        "Ukuran marker",
        min_value=1.0,
        max_value=10.0,
        value=3.5,
        step=0.5
    )

    font_family = st.selectbox(
        "Font",
        ["Times New Roman", "Arial", "DejaVu Serif", "DejaVu Sans"],
        index=0
    )

    base_font_size = st.slider(
        "Ukuran font dasar",
        min_value=8,
        max_value=18,
        value=11
    )


# =========================================================
# Sidebar: Labels and titles
# =========================================================
with st.sidebar:
    st.header("5. Judul dan Label")

    overall_title = st.text_area(
        "Judul utama",
        value=f"Time-Series Visualization of {panel_a_col} and {panel_b_col}",
        height=70
    )

    panel_a_title = st.text_input(
        "Judul Panel A",
        value=f"Panel A. Trend of {panel_a_col} Over Time"
    )

    panel_b_title = st.text_input(
        "Judul Panel B",
        value=f"Panel B. Trend of {panel_b_col} Over Time"
    )

    panel_a_ylabel = st.text_input(
        "Label Y Panel A",
        value=panel_a_col
    )

    panel_b_ylabel = st.text_input(
        "Label Y Panel B",
        value=panel_b_col
    )

    x_label = st.text_input(
        "Label sumbu X",
        value="Date"
    )

    date_format = st.selectbox(
        "Format tanggal sumbu X",
        ["%Y-%m", "%Y", "%d-%m-%Y", "%b %Y", "%Y-%m-%d"],
        index=0
    )

    rotate_xticks = st.slider(
        "Rotasi label tanggal",
        min_value=0,
        max_value=90,
        value=45,
        step=5
    )


# =========================================================
# Sidebar: Export settings
# =========================================================
with st.sidebar:
    st.header("6. Ekspor PNG")

    figsize_width = st.slider(
        "Lebar figure",
        min_value=8.0,
        max_value=20.0,
        value=14.0,
        step=0.5
    )

    figsize_height = st.slider(
        "Tinggi figure",
        min_value=5.0,
        max_value=15.0,
        value=9.0,
        step=0.5
    )

    dpi = st.selectbox(
        "Resolusi PNG",
        [300, 600, 900, 1200],
        index=1
    )


# =========================================================
# Show filtered data
# =========================================================
st.subheader("Data Setelah Diproses dan Difilter")
st.dataframe(filtered_df, use_container_width=True)


# =========================================================
# Create and display chart
# =========================================================
fig = create_two_panel_chart(
    df=filtered_df,
    date_col=date_col,
    panel_a_col=panel_a_col,
    panel_b_col=panel_b_col,
    panel_a_color=panel_a_color,
    panel_b_color=panel_b_color,
    overall_title=overall_title,
    panel_a_title=panel_a_title,
    panel_b_title=panel_b_title,
    panel_a_ylabel=panel_a_ylabel,
    panel_b_ylabel=panel_b_ylabel,
    x_label=x_label,
    figsize_width=figsize_width,
    figsize_height=figsize_height,
    line_width=line_width,
    marker_size=marker_size,
    show_marker=show_marker,
    show_grid=show_grid,
    date_format=date_format,
    rotate_xticks=rotate_xticks,
    font_family=font_family,
    base_font_size=base_font_size
)

st.subheader("Grafik Time Series Dua Panel")
st.pyplot(fig)


# =========================================================
# Download high-resolution PNG
# =========================================================
png_buffer = fig_to_png_bytes(fig, dpi=dpi)

st.download_button(
    label=f"⬇️ Download PNG Resolusi Tinggi ({dpi} DPI)",
    data=png_buffer,
    file_name="two_panel_time_series_publication_style.png",
    mime="image/png"
)

plt.close(fig)