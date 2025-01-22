from fastapi import FastAPI, HTTPException
import pandas as pd

app = FastAPI()

# Quran Data load function
def load_surahs():
    try:
        file_path = "quran_data.xlsx"  # Ensure this file is in the same directory
        return pd.read_excel(file_path)
    except Exception as e:
        raise RuntimeError(f"Error loading Quran data: {e}")

# Load Quran data at the start
quran_data = load_surahs()

@app.get("/")
async def root():
    return {"message": "Welcome to the Quran Surah API"}

@app.get("/surah/{sura_id}")
@app.get("/surah/{sura_id}/{additional}")
@app.get("/surah/{sura_id}/{aya_no}")
@app.get("/surah/{sura_id}/{aya_no}/{additional}")
@app.get("/surah/{sura_id}/info")
async def get_surah(sura_id: int, aya_no: int = None, additional: str = None):
    # Filter data for the given Surah
    surah_data = quran_data[quran_data["SuraID"] == sura_id]

    if surah_data.empty:
        raise HTTPException(
            status_code=404,
            detail=f"Surah ID {sura_id} not found."
        )

    # If specific Aya number is provided
    if aya_no is not None:
        ayah_data = surah_data[surah_data["AyaNo"] == aya_no]
        if ayah_data.empty:
            raise HTTPException(
                status_code=404,
                detail=f"Ayah {aya_no} in Surah {sura_id} not found."
            )
    else:
        ayah_data = surah_data  # Full Surah data if no Aya number is specified

    # Arabic text
    arabic_text = ayah_data[["AyaNo", "Arabic Text"]].to_dict(orient="records")

    # Handle translation or author
    translation = None
    if additional:
        additional = additional.lower()

        if additional == "urdu":
            column_name = "Fateh Muhammad Jalandhri"
        elif additional == "english":
            column_name = "Saheeh International"
        else:
            # Handle specific author names
            if additional in quran_data.columns:
                column_name = additional
            else:
                raise HTTPException(
                    status_code=404,
                    detail=f"Author/Translator '{additional}' not found in the dataset."
                )

        # Check if translation column exists in data
        if column_name not in quran_data.columns:
            raise HTTPException(
                status_code=404,
                detail=f"Translator '{column_name}' not found in the dataset."
            )

        translation = ayah_data[["AyaNo", column_name]].to_dict(orient="records")

    # Handle surah info
    if additional == "info":
        surah_info = {
            "Surah Name": surah_data.iloc[0]["SurahNameU"],
            "Total Ayahs": surah_data["AyaNo"].nunique(),
            "Total Rukus": surah_data["RukuNo"].nunique(),
            "Makki/Madani": "Makki" if surah_data.iloc[0]["Makki"] else "Madani",
            "Tartibi Number": surah_data.iloc[0]["TartibiNumber"],
            "Nuzuli Number": surah_data.iloc[0]["NuzuliNumber"],
            "Surah Meaning": surah_data.iloc[0]["SurahNameMeaning"]
        }
        return surah_info

    # Prepare response
    response = {
        "Surah Name": surah_data.iloc[0]["SurahNameU"],
        "Arabic Text with Translation": []
    }

    # Add each Aya's Arabic text and its translation if available
    for i, row in enumerate(arabic_text):
        ayah_translation = None
        if translation:
            ayah_translation = translation[i]
        response["Arabic Text with Translation"].append({
            "AyaNo": row["AyaNo"],
            "Arabic Text": row["Arabic Text"],
            "Translation": ayah_translation or "Translation not available"
        })

    return response
