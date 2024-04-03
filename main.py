from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
import pandas as pd
import Levenshtein
import pickle
import textdistance

model_path = "/workspace/pickle_try/xgb_model.pkl"
with open(model_path, "rb") as file:
    model = pickle.load(file)

DATABASE_URL = "postgresql://admin:LocalPasswordOnly@localhost:5432/postgres"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

app = FastAPI()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def calculate_features(rue_init, prop_lev):
    if not rue_init or not prop_lev:
        raise ValueError("Les chaînes de caractères ne doivent pas être vides.")

    features_dict = {
        "damerau_levenshtein": [textdistance.damerau_levenshtein.normalized_similarity(rue_init, prop_lev)],
        "jaro_winkler": [textdistance.jaro_winkler(rue_init, prop_lev)],
        "jaro": [textdistance.jaro(rue_init, prop_lev)],
        "sorensen_dice": [textdistance.sorensen_dice(rue_init, prop_lev)],
        "lcs": [textdistance.lcsstr.normalized_similarity(rue_init, prop_lev)]
    }

    features_df = pd.DataFrame.from_dict(features_dict)
    return features_df



async def couple_cp_ville_existe(code_postal: int, nom_commune: str, db: Session) -> bool:
    sql_couple_exists = """
        SELECT EXISTS (
            SELECT 1 FROM cp_ville
            WHERE code_postal = :code_postal
            AND LOWER(nom_commune) = LOWER(:nom_commune)
        )
    """
    return db.execute(text(sql_couple_exists), {"code_postal": code_postal, "nom_commune": nom_commune.lower()}).scalar()

async def recuperer_rues_cp_ville(code_postal: int, nom_commune: str, db: Session) -> pd.DataFrame:
    sql_rues = """
        SELECT nom_afnor FROM cp_ville_rue
        WHERE code_postal = :code_postal
        AND LOWER(nom_commune) = LOWER(:nom_commune)
    """
    rues_result = db.execute(text(sql_rues), {"code_postal": code_postal, "nom_commune": nom_commune.lower()}).fetchall()
    return pd.DataFrame(rues_result, columns=['nom_afnor'])


from sqlalchemy import text
import pandas as pd


@app.get("/verify_cp_ville_rue/")
async def verify_cp_ville_rue(code_postal: int, nom_commune: str, nom_rue: str, db: Session = Depends(get_db)):
    try:
        couple_exists = await couple_cp_ville_existe(code_postal, nom_commune, db)
        rues_df = await recuperer_rues_cp_ville(code_postal, nom_commune, db)
        
        if nom_rue.lower() in rues_df['nom_afnor'].str.lower().values:
            return {"message": "La rue existe pour le code postal et la ville donnés.", "couple_cp_ville_existe": couple_exists}
        else:
            if not rues_df.empty:
                similarity_scores = []
                
                for x in rues_df['nom_afnor']:
                    features = await calculate_features(nom_rue, x)
                    # Afficher les caractéristiques calculées pour la paire actuelle
                    print(f"Caractéristiques pour '{nom_rue}' vs '{x}':", features.to_dict(orient='records')[0])
                    
                    # Prédiction du score de similarité pour la paire actuelle
                    score = model.predict_proba(features)[:, 1][0]  # Prendre le score de la classe "similaire"
                    similarity_scores.append(score)
                    # Afficher le score de similarité calculé
                    print(f"Score de similarité pour '{nom_rue}' vs '{x}': {score}")
                
                # Ajout des scores de similarité au DataFrame des rues
                rues_df['similarity_score'] = similarity_scores
                
                # Tri du DataFrame par score de similarité en ordre décroissant
                rues_df_sorted = rues_df.sort_values(by='similarity_score', ascending=False)
                top_similar_rues_info = rues_df_sorted.head(10).to_dict(orient='records')
                
                return {
                    "message": "La rue spécifiée n'existe pas pour le couple code postal-ville donné, voici les suggestions les plus proches.",
                    "couple_cp_ville_existe": couple_exists,
                    "top_suggestions": top_similar_rues_info
                }
            else:
                return {"message": "Aucune rue trouvée pour le couple code postal-ville spécifié.", "couple_cp_ville_existe": couple_exists}
    except Exception as e:
        print(f"Erreur : {e}")
        raise HTTPException(status_code=500, detail="Erreur interne du serveur")

@app.get("/test_calculate_features/")
async def test_calculate_features():
    rue_init = "ABDVS"
    prop_lev = "BSDF"
    features_df = calculate_features(rue_init, prop_lev)
    # Conversion du DataFrame en dictionnaire pour la sortie JSON
    features_dict = features_df.to_dict(orient='records')[0]
    return {"features": features_dict}

@app.get("/test_similarity/")
async def test_similarity():
    rue_init = "Avenue"
    prop_lev = "Avnue"
    
    damerau_levenshtein = textdistance.damerau_levenshtein.normalized_similarity(rue_init, prop_lev)
    jaro_winkler = textdistance.jaro_winkler(rue_init, prop_lev)
    jaro = textdistance.jaro(rue_init, prop_lev)
    sorensen_dice = textdistance.sorensen_dice(rue_init, prop_lev)
    lcs = textdistance.lcsstr.normalized_similarity(rue_init, prop_lev)
    
    return {
        "damerau_levenshtein": damerau_levenshtein,
        "jaro_winkler": jaro_winkler,
        "jaro": jaro,
        "sorensen_dice": sorensen_dice,
        "lcs": lcs
    }
