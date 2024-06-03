from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
import pandas as pd
import Levenshtein
import pickle
import textdistance
import logging

# Configuration de la journalisation
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

model_path = "/workspace/pickle_try/xgb_model.pkl"
with open(model_path, "rb") as file:
    model = pickle.load(file)
    logger.info("Model loaded successfully from %s", model_path)

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
    
    logger.debug("Calculating features for: %s vs %s", rue_init, prop_lev)
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
    result = db.execute(text(sql_couple_exists), {"code_postal": code_postal, "nom_commune": nom_commune.lower()}).scalar()
    logger.info("Couple code postal %d and ville %s exists: %s", code_postal, nom_commune, result)
    return result

async def recuperer_rues_cp_ville(code_postal: int, nom_commune: str, db: Session) -> pd.DataFrame:
    sql_rues = """
        SELECT nom_afnor FROM cp_ville_rue
        WHERE code_postal = :code_postal
        AND LOWER(nom_commune) = LOWER(:nom_commune)
    """
    rues_result = db.execute(text(sql_rues), {"code_postal": code_postal, "nom_commune": nom_commune.lower()}).fetchall()
    return pd.DataFrame(rues_result, columns=['nom_afnor'])

@app.get("/verify_cp_ville_rue/")
async def verify_cp_ville_rue(code_postal: int, nom_commune: str, nom_rue: str, db: Session = Depends(get_db)):
    try:
        logger.info("Verifying rue %s for code postal %d and ville %s", nom_rue, code_postal, nom_commune)
        couple_exists = await couple_cp_ville_existe(code_postal, nom_commune, db)
        rues_df = await recuperer_rues_cp_ville(code_postal, nom_commune, db)
        
        if nom_rue.lower() in rues_df['nom_afnor'].str.lower().values:
            logger.info("Rue %s exists in database", nom_rue)
            return {"message": "La rue existe pour le code postal et la ville donnés.", "couple_cp_ville_existe": couple_exists}
        else:
            if not rues_df.empty:
                similarity_scores = []
                
                for x in rues_df['nom_afnor']:
                    features = await calculate_features(nom_rue, x)
                    logger.debug("Features for '%s' vs '%s': %s", nom_rue, x, features.to_dict(orient='records')[0])
                    
                    score = model.predict_proba(features)[:, 1][0]
                    similarity_scores.append(score)
                    logger.debug("Similarity score for '%s' vs '%s': %f", nom_rue, x, score)
                
                rues_df['similarity_score'] = similarity_scores
                rues_df_sorted = rues_df.sort_values(by='similarity_score', ascending=False)
                top_similar_rues_info = rues_df_sorted.head(10).to_dict(orient='records')
                
                logger.info("Top 10 similar rues for '%s': %s", nom_rue, top_similar_rues_info)
                return {
                    "message": "La rue spécifiée n'existe pas pour le couple code postal-ville donné, voici les suggestions les plus proches.",
                    "couple_cp_ville_existe": couple_exists,
                    "top_suggestions": top_similar_rues_info
                }
            else:
                logger.warning("No rues found for code postal %d and ville %s", code_postal, nom_commune)
                return {"message": "Aucune rue trouvée pour le couple code postal-ville spécifié.", "couple_cp_ville_existe": couple_exists}
    except Exception as e:
        logger.error("Erreur : %s", e)
        raise HTTPException(status_code=500, detail="Erreur interne du serveur")

@app.get("/verify_address/")
async def verify_address(code_postal: int, nom_commune: str, nom_rue: str, numero: int, rep: str = None, db: Session = Depends(get_db)):
    try:
        logger.info("Verifying address for code postal %d, ville %s, rue %s, numero %d, rep %s", 
                    code_postal, nom_commune, nom_rue, numero, rep)
        
        # First, call the existing verify_cp_ville_rue endpoint to check if the street exists
        rue_check = await verify_cp_ville_rue(code_postal, nom_commune, nom_rue, db)
        
        if "La rue existe" in rue_check["message"]:
            # If the street exists, check the number and repetition
            sql_address = """
                SELECT EXISTS (
                    SELECT 1 FROM table_name
                    WHERE code_postal = :code_postal
                    AND LOWER(nom_commune) = LOWER(:nom_commune)
                    AND LOWER(nom_afnor) = LOWER(:nom_rue)
                    AND numero = :numero
                    AND (:rep IS NULL OR LOWER(rep) = LOWER(:rep))
                )
            """
            address_exists = db.execute(text(sql_address), {
                "code_postal": code_postal,
                "nom_commune": nom_commune.lower(),
                "nom_rue": nom_rue.lower(),
                "numero": numero,
                "rep": rep.lower() if rep else None
            }).scalar()
            
            if address_exists:
                return {"message": "L'adresse existe.", "address_exists": True}
            else:
                return {"message": "Le numéro de rue ou la répétition n'existe pas pour l'adresse spécifiée.", "address_exists": False}
        else:
            return rue_check
    except Exception as e:
        logger.error("Erreur : %s", e)
        raise HTTPException(status_code=500, detail="Erreur interne du serveur")



@app.get("/test_calculate_features/")
async def test_calculate_features():
    rue_init = "ABDVS"
    prop_lev = "BSDF"
    features_df = await calculate_features(rue_init, prop_lev)
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
