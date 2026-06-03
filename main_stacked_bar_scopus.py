import streamlit as st
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter
from io import BytesIO


# =========================================================
# Page configuration
# =========================================================
st.set_page_config(
    page_title="Stacked Bar Chart - Scopus Style",
    page_icon="📊",
    layout="wide"
)

st.markdown(
    """
    ### Developed by Prana Ugiana Gio

    **Website:** [pranaugi.com](https://pranaugi.com/)

    **YouTube:** [STATKOMAT](https://www.youtube.com/@STATKOMAT)

    **Online Store:** [lynk.id/statkomat](https://lynk.id/statkomat)

    ---
    """
)


# =========================================================
# Color palettes
# =========================================================
COLOR_PALETTES = {
    "Scopus Orange - Blue - Green": [
        "#E97132", "#4472C4", "#70AD47", "#FFC000", "#7030A0",
        "#A5A5A5", "#C00000", "#00A6A6", "#595959", "#ED7D31"
    ],
    "Academic Blue": [
        "#1F4E79", "#5B9BD5", "#70AD47", "#A9D18E", "#4472C4",
        "#2F5597", "#203864", "#9DC3E6", "#548235", "#375623"
    ],
    "Nature Green": [
        "#375623", "#548235", "#70AD47", "#A9D18E", "#C5E0B4",
        "#806000", "#BF9000", "#FFC000", "#7F7F7F", "#595959"
    ],
    "Warm Publication": [
        "#C55A11", "#E97132", "#F4B183", "#FFD966", "#A64D79",
        "#7030A0", "#8064A2", "#B4A7D6", "#666666", "#999999"
    ],
    "Black - Gray": [
        "#000000", "#404040", "#666666", "#808080", "#A6A6A6",
        "#BFBFBF", "#D9D9D9", "#595959", "#262626", "#8C8C8C"
    ],
    "High Contrast": [
        "#003f5c", "#bc5090", "#ffa600", "#58508d", "#ff6361",
        "#2f4b7c", "#665191", "#a05195", "#d45087", "#f95d6a"
    ]
}


# =========================================================
# Helper functions
# =========================================================
def read_uploaded_file(uploaded_file):
    """Read CSV/XLSX/XLS uploaded in Streamlit."""
    file_name = uploaded_file.name.lower()

    if file_name.endswith(".csv"):
        return pd.read_csv(uploaded_file)

    if file_name.endswith(".xlsx"):
        return pd.read_excel(uploaded_file, engine="openpyxl")

    if file_name.endswith(".xls"):
        return pd.read_excel(uploaded_file)

    raise ValueError("Format file tidak didukung. Gunakan CSV, XLSX, atau XLS.")


@st.cache_data
def make_sample_data():
    """Sample data dengan struktur mirip data saham tahunan."""
    rng = np.random.default_rng(2026)
    years = np.repeat(np.arange(2019, 2026), 240)
    directions = rng.choice(
        ["Positive", "Negative", "Neutral"],
        size=len(years),
        p=[0.47, 0.45, 0.08]
    )

    return pd.DataFrame({
        "Year": years,
        "Daily Stock Return Direction": directions,
        "Price Anomaly Category": rng.choice(
            ["Normal", "Moderate Anomaly", "Extreme Anomaly"],
            size=len(years),
            p=[0.80, 0.15, 0.05]
        ),
        "Strong Anomaly": rng.choice(["No", "Yes"], size=len(years), p=[0.88, 0.12])
    })


def get_default_column(columns, preferred_names, fallback_index=0):
    """Return default column based on exact preferred names, then fallback."""
    for name in preferred_names:
        if name in columns:
            return name

    lower_map = {col.lower(): col for col in columns}
    for name in preferred_names:
        if name.lower() in lower_map:
            return lower_map[name.lower()]

    return columns[min(fallback_index, len(columns) - 1)]


def unique_as_string(series):
    """Return unique values as strings, preserving first-seen order."""
    return pd.Series(series.dropna().astype(str).unique()).tolist()


def safe_sort(values, reverse=False):
    """Sort values numerically/datetime when possible, otherwise alphabetically."""
    values = list(values)

    numeric_values = pd.to_numeric(pd.Series(values), errors="coerce")
    if numeric_values.notna().all():
        paired = sorted(zip(values, numeric_values), key=lambda x: x[1], reverse=reverse)
        return [x[0] for x in paired]

    datetime_values = pd.to_datetime(pd.Series(values), errors="coerce")
    if datetime_values.notna().all():
        paired = sorted(zip(values, datetime_values), key=lambda x: x[1], reverse=reverse)
        return [x[0] for x in paired]

    return sorted(values, key=lambda x: str(x).lower(), reverse=reverse)


def parse_custom_order(order_text, available_values):
    """Parse comma-separated custom order and append remaining values."""
    available_values = list(available_values)
    typed_values = [item.strip() for item in order_text.split(",") if item.strip()]

    ordered = []
    for item in typed_values:
        if item in available_values and item not in ordered:
            ordered.append(item)

    remaining = [item for item in available_values if item not in ordered]
    return ordered + remaining


def reorder_table(freq_table, x_order_option, category_order_option, x_custom_text, cat_custom_text):
    """Reorder rows and columns based on user-selected ordering rules."""
    x_values = list(freq_table.index)
    cat_values = list(freq_table.columns)

    row_totals = freq_table.sum(axis=1)
    col_totals = freq_table.sum(axis=0)

    if x_order_option == "Naik (A-Z / kecil-besar)":
        x_order = safe_sort(x_values, reverse=False)
    elif x_order_option == "Turun (Z-A / besar-kecil)":
        x_order = safe_sort(x_values, reverse=True)
    elif x_order_option == "Total frekuensi tertinggi":
        x_order = row_totals.sort_values(ascending=False).index.tolist()
    elif x_order_option == "Total frekuensi terendah":
        x_order = row_totals.sort_values(ascending=True).index.tolist()
    elif x_order_option == "Custom":
        x_order = parse_custom_order(x_custom_text, x_values)
    else:
        x_order = x_values

    if category_order_option == "Naik (A-Z / kecil-besar)":
        cat_order = safe_sort(cat_values, reverse=False)
    elif category_order_option == "Turun (Z-A / besar-kecil)":
        cat_order = safe_sort(cat_values, reverse=True)
    elif category_order_option == "Total frekuensi tertinggi":
        cat_order = col_totals.sort_values(ascending=False).index.tolist()
    elif category_order_option == "Total frekuensi terendah":
        cat_order = col_totals.sort_values(ascending=True).index.tolist()
    elif category_order_option == "Custom":
        cat_order = parse_custom_order(cat_custom_text, cat_values)
    else:
        cat_order = cat_values

    return freq_table.loc[x_order, cat_order]


def build_stacked_tables(df, x_col, category_col, value_mode, percentage_basis):
    """Create frequency table and plotting table."""
    working_df = df[[x_col, category_col]].copy()
    working_df = working_df.dropna(subset=[x_col, category_col])

    working_df["_x_value"] = working_df[x_col].astype(str)
    working_df["_category_value"] = working_df[category_col].astype(str)

    freq_table = (
        working_df
        .groupby(["_x_value", "_category_value"], sort=False)
        .size()
        .unstack(fill_value=0)
    )

    if value_mode == "Persentase":
        if percentage_basis == "Per kelompok sumbu X / 100% stacked":
            denominator = freq_table.sum(axis=1).replace(0, np.nan)
            plot_table = freq_table.div(denominator, axis=0) * 100
        else:
            denominator = freq_table.values.sum()
            plot_table = freq_table / denominator * 100 if denominator else freq_table * 0
    else:
        plot_table = freq_table.astype(float)

    return freq_table, plot_table


def format_display_table(table, value_mode):
    """Format table for preview."""
    if value_mode == "Persentase":
        return table.apply(lambda col: col.map(lambda x: f"{x:.2f}%"))
    return table.astype(int)


def apply_publication_style(font_family, base_font_size):
    plt.rcParams["font.family"] = font_family
    plt.rcParams["font.size"] = base_font_size
    plt.rcParams["axes.labelsize"] = base_font_size + 1
    plt.rcParams["axes.titlesize"] = base_font_size + 3
    plt.rcParams["legend.fontsize"] = base_font_size
    plt.rcParams["xtick.labelsize"] = base_font_size
    plt.rcParams["ytick.labelsize"] = base_font_size
    plt.rcParams["figure.facecolor"] = "white"
    plt.rcParams["axes.facecolor"] = "white"


def create_stacked_bar_chart(
    plot_table,
    category_colors,
    value_mode,
    percentage_basis,
    title,
    subtitle,
    x_label,
    y_label,
    legend_title,
    figsize_width,
    figsize_height,
    bar_width,
    edge_color,
    edge_width,
    show_grid,
    show_value_labels,
    label_min_value,
    x_tick_rotation,
    legend_position,
    font_family,
    base_font_size,
    title_font_size,
    axis_label_font_size,
    tick_font_size,
    legend_font_size,
    data_label_font_size,
    title_color,
    subtitle_color,
    axis_label_color,
    tick_color,
    legend_text_color,
    data_label_color
):
    """Create publication-style stacked bar chart."""
    apply_publication_style(font_family, base_font_size)

    fig, ax = plt.subplots(figsize=(figsize_width, figsize_height))

    x_labels = plot_table.index.tolist()
    x_positions = np.arange(len(x_labels))
    bottom = np.zeros(len(plot_table))

    for category in plot_table.columns:
        values = plot_table[category].fillna(0).to_numpy(dtype=float)
        color = category_colors.get(category, "#808080")

        ax.bar(
            x_positions,
            values,
            bottom=bottom,
            label=category,
            color=color,
            width=bar_width,
            edgecolor=edge_color,
            linewidth=edge_width
        )

        if show_value_labels:
            for i, value in enumerate(values):
                if value <= 0 or value < label_min_value:
                    continue

                label = f"{value:.2f}%" if value_mode == "Persentase" else f"{int(round(value))}"
                ax.text(
                    x_positions[i],
                    bottom[i] + value / 2,
                    label,
                    ha="center",
                    va="center",
                    fontsize=data_label_font_size,
                    color=data_label_color
                )

        bottom += values

    ax.set_title(title, fontsize=title_font_size, fontweight="bold", color=title_color, pad=18)

    if subtitle.strip():
        ax.text(
            0.5,
            1.01,
            subtitle,
            transform=ax.transAxes,
            ha="center",
            va="bottom",
            fontsize=max(title_font_size - 3, 8),
            color=subtitle_color
        )

    ax.set_xlabel(x_label, fontsize=axis_label_font_size, color=axis_label_color, labelpad=10)
    ax.set_ylabel(y_label, fontsize=axis_label_font_size, color=axis_label_color, labelpad=10)

    ax.set_xticks(x_positions)
    ax.set_xticklabels(x_labels, rotation=x_tick_rotation, ha="right" if x_tick_rotation else "center")

    ax.tick_params(axis="x", colors=tick_color, labelsize=tick_font_size)
    ax.tick_params(axis="y", colors=tick_color, labelsize=tick_font_size)

    if value_mode == "Persentase":
        ax.yaxis.set_major_formatter(PercentFormatter(xmax=100, decimals=0))
        if percentage_basis == "Per kelompok sumbu X / 100% stacked":
            ax.set_ylim(0, 100)

    if show_grid:
        ax.grid(axis="y", linestyle="--", linewidth=0.6, alpha=0.45)
        ax.set_axisbelow(True)

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_linewidth(0.8)
    ax.spines["bottom"].set_linewidth(0.8)

    if legend_position == "Di luar kanan":
        legend = ax.legend(
            title=legend_title,
            loc="upper left",
            bbox_to_anchor=(1.02, 1),
            frameon=True,
            fontsize=legend_font_size,
            title_fontsize=legend_font_size
        )
    elif legend_position == "Bawah":
        legend = ax.legend(
            title=legend_title,
            loc="upper center",
            bbox_to_anchor=(0.5, -0.18),
            ncol=min(4, max(1, len(plot_table.columns))),
            frameon=True,
            fontsize=legend_font_size,
            title_fontsize=legend_font_size
        )
    else:
        legend = ax.legend(
            title=legend_title,
            loc="upper right",
            frameon=True,
            fontsize=legend_font_size,
            title_fontsize=legend_font_size
        )

    for text in legend.get_texts():
        text.set_color(legend_text_color)
    legend.get_title().set_color(legend_text_color)

    fig.tight_layout()
    return fig


def fig_to_png_bytes(fig, dpi, transparent_background):
    buffer = BytesIO()
    fig.savefig(
        buffer,
        dpi=dpi,
        format="png",
        bbox_inches="tight",
        facecolor="none" if transparent_background else "white",
        transparent=transparent_background
    )
    buffer.seek(0)
    return buffer


# =========================================================
# App title
# =========================================================
st.title("📊 Stacked Bar Chart Publication-Style")
st.caption(
    "Aplikasi untuk membuat grafik batang stacked ala publikasi/Scopus dari data kategori, "
    "dengan pilihan frekuensi atau persentase dan ekspor PNG resolusi tinggi."
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
    st.info("Jika membaca Excel .xlsx gagal, jalankan: python -m pip install openpyxl")
    st.stop()

if df.empty:
    st.error("Data kosong.")
    st.stop()

columns = df.columns.tolist()

# =========================================================
# Data preview
# =========================================================
st.subheader("Preview Data")
st.dataframe(df.head(30), use_container_width=True)


# =========================================================
# Sidebar: Column selection
# =========================================================
default_x_col = get_default_column(columns, ["Year", "Tahun", "Date", "Tanggal"], fallback_index=0)
default_cat_col = get_default_column(
    columns,
    ["Daily Stock Return Direction", "Return Direction", "Direction", "Kategori"],
    fallback_index=1 if len(columns) > 1 else 0
)

with st.sidebar:
    st.header("2. Pilih Variabel")

    x_col = st.selectbox(
        "Variabel sumbu X",
        columns,
        index=columns.index(default_x_col)
    )

    category_col = st.selectbox(
        "Variabel kategori / isi batang stacked",
        columns,
        index=columns.index(default_cat_col)
    )

    value_mode = st.radio(
        "Tampilkan nilai sebagai",
        ["Frekuensi", "Persentase"],
        horizontal=True
    )

    percentage_basis = st.selectbox(
        "Basis persentase",
        ["Per kelompok sumbu X / 100% stacked", "Dari total seluruh data"],
        index=0,
        disabled=value_mode == "Frekuensi"
    )

if x_col == category_col:
    st.error("Variabel sumbu X dan variabel kategori tidak boleh sama.")
    st.stop()

# =========================================================
# Build frequency and percentage tables
# =========================================================
try:
    freq_table, plot_table_unordered = build_stacked_tables(
        df=df,
        x_col=x_col,
        category_col=category_col,
        value_mode=value_mode,
        percentage_basis=percentage_basis
    )
except Exception as e:
    st.error(f"Gagal membuat tabel stacked: {e}")
    st.stop()

if freq_table.empty:
    st.error("Tidak ada data valid setelah nilai kosong dihapus.")
    st.stop()

# =========================================================
# Sidebar: Category order
# =========================================================
with st.sidebar:
    st.header("3. Urutan Kategorisasi")

    order_options = [
        "Sesuai data",
        "Naik (A-Z / kecil-besar)",
        "Turun (Z-A / besar-kecil)",
        "Total frekuensi tertinggi",
        "Total frekuensi terendah",
        "Custom"
    ]

    x_order_option = st.selectbox(
        "Urutan sumbu X",
        order_options,
        index=1
    )

    x_custom_text = ""
    if x_order_option == "Custom":
        x_custom_text = st.text_area(
            "Urutan custom sumbu X, pisahkan dengan koma",
            value=", ".join(freq_table.index.astype(str).tolist()),
            height=90
        )

    category_order_option = st.selectbox(
        "Urutan kategori stacked",
        order_options,
        index=0
    )

    cat_custom_text = ""
    if category_order_option == "Custom":
        cat_custom_text = st.text_area(
            "Urutan custom kategori, pisahkan dengan koma",
            value=", ".join(freq_table.columns.astype(str).tolist()),
            height=90
        )

freq_table_ordered = reorder_table(
    freq_table=freq_table,
    x_order_option=x_order_option,
    category_order_option=category_order_option,
    x_custom_text=x_custom_text,
    cat_custom_text=cat_custom_text
)

if value_mode == "Persentase":
    if percentage_basis == "Per kelompok sumbu X / 100% stacked":
        denominator = freq_table_ordered.sum(axis=1).replace(0, np.nan)
        plot_table = freq_table_ordered.div(denominator, axis=0) * 100
    else:
        denominator = freq_table_ordered.values.sum()
        plot_table = freq_table_ordered / denominator * 100 if denominator else freq_table_ordered * 0
else:
    plot_table = freq_table_ordered.astype(float)

# =========================================================
# Sidebar: Chart style
# =========================================================
with st.sidebar:
    st.header("4. Warna dan Gaya Grafik")

    color_palette_name = st.selectbox(
        "Palet warna",
        list(COLOR_PALETTES.keys()),
        index=0
    )

    selected_palette = COLOR_PALETTES[color_palette_name]

    st.markdown("**Warna setiap kategori**")
    category_colors = {}
    for i, category in enumerate(plot_table.columns):
        default_color = selected_palette[i % len(selected_palette)]
        category_colors[category] = st.color_picker(
            f"Warna: {category}",
            default_color
        )

    show_grid = st.checkbox("Tampilkan grid horizontal", value=True)
    show_value_labels = st.checkbox("Tampilkan label nilai di batang", value=True)

    default_label_threshold = 4.0 if value_mode == "Persentase" else 1.0
    label_min_value = st.number_input(
        "Minimal nilai yang diberi label",
        min_value=0.0,
        value=default_label_threshold,
        step=1.0
    )

    bar_width = st.slider(
        "Lebar batang",
        min_value=0.20,
        max_value=1.00,
        value=0.72,
        step=0.02
    )

    edge_color = st.color_picker("Warna garis tepi batang", "#FFFFFF")
    edge_width = st.slider(
        "Ketebalan garis tepi batang",
        min_value=0.0,
        max_value=2.0,
        value=0.6,
        step=0.1
    )

    legend_position = st.selectbox(
        "Posisi legenda",
        ["Di luar kanan", "Di dalam kanan atas", "Bawah"],
        index=0
    )

# =========================================================
# Sidebar: Text settings
# =========================================================
with st.sidebar:
    st.header("5. Ukuran dan Warna Teks")

    font_family = st.selectbox(
        "Font",
        ["Times New Roman", "Arial", "DejaVu Serif", "DejaVu Sans"],
        index=1
    )

    base_font_size = st.slider("Ukuran font dasar", 8, 24, 12)
    title_font_size = st.slider("Ukuran judul", 10, 36, 18)
    axis_label_font_size = st.slider("Ukuran label sumbu", 8, 28, 13)
    tick_font_size = st.slider("Ukuran angka/kategori sumbu", 6, 24, 11)
    legend_font_size = st.slider("Ukuran legenda", 6, 24, 10)
    data_label_font_size = st.slider("Ukuran label nilai batang", 6, 22, 9)

    title_color = st.color_picker("Warna judul", "#000000")
    subtitle_color = st.color_picker("Warna subjudul", "#595959")
    axis_label_color = st.color_picker("Warna label sumbu", "#000000")
    tick_color = st.color_picker("Warna teks sumbu", "#000000")
    legend_text_color = st.color_picker("Warna teks legenda", "#000000")
    data_label_color = st.color_picker("Warna label nilai batang", "#000000")

# =========================================================
# Sidebar: Labels, title, export
# =========================================================
with st.sidebar:
    st.header("6. Judul, Label, dan Ekspor")

    default_title = f"Stacked Bar Chart of {category_col} by {x_col}"
    title = st.text_area("Judul grafik", value=default_title, height=70)

    subtitle = st.text_input(
        "Subjudul",
        value="Frequency distribution" if value_mode == "Frekuensi" else "Percentage distribution"
    )

    x_label = st.text_input("Label sumbu X", value=x_col)
    y_label_default = "Frekuensi" if value_mode == "Frekuensi" else "Persentase (%)"
    y_label = st.text_input("Label sumbu Y", value=y_label_default)
    legend_title = st.text_input("Judul legenda", value=category_col)

    x_tick_rotation = st.slider("Rotasi teks sumbu X", 0, 90, 0, step=5)

    figsize_width = st.slider(
        "Lebar grafik / figure",
        min_value=6.0,
        max_value=24.0,
        value=13.0,
        step=0.5
    )

    figsize_height = st.slider(
        "Tinggi grafik / figure",
        min_value=4.0,
        max_value=18.0,
        value=7.5,
        step=0.5
    )

    dpi = st.selectbox(
        "Resolusi PNG / DPI",
        [300, 600, 900, 1200],
        index=1
    )

    transparent_background = st.checkbox("Background PNG transparan", value=False)

# =========================================================
# Summary cards
# =========================================================
left_col, mid_col, right_col = st.columns(3)
with left_col:
    st.metric("Jumlah bar sumbu X", len(plot_table.index))
with mid_col:
    st.metric("Jumlah kategori stacked", len(plot_table.columns))
with right_col:
    st.metric("Total observasi valid", int(freq_table_ordered.values.sum()))

# =========================================================
# Show processed tables
# =========================================================
st.subheader("Tabel Frekuensi")
st.dataframe(freq_table_ordered.astype(int), use_container_width=True)

st.subheader("Tabel yang Digunakan untuk Grafik")
st.dataframe(format_display_table(plot_table, value_mode), use_container_width=True)

# =========================================================
# Create and display chart
# =========================================================
fig = create_stacked_bar_chart(
    plot_table=plot_table,
    category_colors=category_colors,
    value_mode=value_mode,
    percentage_basis=percentage_basis,
    title=title,
    subtitle=subtitle,
    x_label=x_label,
    y_label=y_label,
    legend_title=legend_title,
    figsize_width=figsize_width,
    figsize_height=figsize_height,
    bar_width=bar_width,
    edge_color=edge_color,
    edge_width=edge_width,
    show_grid=show_grid,
    show_value_labels=show_value_labels,
    label_min_value=label_min_value,
    x_tick_rotation=x_tick_rotation,
    legend_position=legend_position,
    font_family=font_family,
    base_font_size=base_font_size,
    title_font_size=title_font_size,
    axis_label_font_size=axis_label_font_size,
    tick_font_size=tick_font_size,
    legend_font_size=legend_font_size,
    data_label_font_size=data_label_font_size,
    title_color=title_color,
    subtitle_color=subtitle_color,
    axis_label_color=axis_label_color,
    tick_color=tick_color,
    legend_text_color=legend_text_color,
    data_label_color=data_label_color
)

st.subheader("Grafik Batang Stacked")
st.pyplot(fig, use_container_width=False)

# =========================================================
# Download high-resolution PNG
# =========================================================
png_buffer = fig_to_png_bytes(
    fig=fig,
    dpi=dpi,
    transparent_background=transparent_background
)

st.download_button(
    label=f"⬇️ Download PNG Resolusi Tinggi ({dpi} DPI)",
    data=png_buffer,
    file_name="stacked_bar_chart_scopus_style.png",
    mime="image/png"
)

plt.close(fig)
