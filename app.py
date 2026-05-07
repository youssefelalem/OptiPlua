from simulator import ScheduleSimulator
import streamlit as st
import pandas as pd

# إعدادات الصفحة
st.set_page_config(page_title="OptiPlua Dashboard", layout="wide")

st.title("🚀 OptiPlua — Système d'Optimisation d'Emplois du Temps")
st.markdown("---")

# ==========================================
# 1. قسم استيراد البيانات (Data Management)
# ==========================================
st.sidebar.header("📂 Importation des Données")
st.sidebar.info("Veuillez importer les 3 fichiers (CSV) pour activer la simulation.")

# أزرار رفع الملفات الثلاثة
file_profs = st.sidebar.file_uploader("1. Liste des Enseignants", type=['csv'])
file_salles = st.sidebar.file_uploader("2. Liste des Salles", type=['csv'])
file_classes = st.sidebar.file_uploader("3. Liste des Classes", type=['csv'])

# ==========================================
# 2. الحماية والتحقق من الملفات
# ==========================================
# هذا الشرط يمنع ظهور زر التوليد ويحمي المنصة من الانهيار إذا لم تكتمل الملفات
if file_profs and file_salles and file_classes:
    st.sidebar.success("✅ Tous les fichiers sont chargés !")
    
    # قراءة الملفات التي رفعها المدير
    df_profs = pd.read_csv(file_profs)
    df_salles = pd.read_csv(file_salles)
    df_classes = pd.read_csv(file_classes)
    
    # عرض نظرة سريعة للمدير ليتأكد من بياناته
    with st.expander("👁️ Voir l'aperçu des données importées"):
        st.write("**Enseignants:**", df_profs.head(3))
        st.write("**Salles:**", df_salles.head(3))
        st.write("**Classes:**", df_classes.head(3))

    # ==========================================
    # 3. قسم التوليد والربط مع المحرك
    # ==========================================
    st.header("⚙️ Paramètres et Génération")
    n_candidates = st.slider("Nombre de candidats à générer", 10, 100, 50)
    
    if st.button("🚀 Générer les Meilleurs Emplois du Temps", type="primary"):
        with st.spinner("⏳ Génération et évaluation en cours... Veuillez patienter."):
            
            # 1. استدعاء المحرك
            sim = ScheduleSimulator()
            
            # 2. حقن المحرك بالبيانات الجديدة التي رفعها المدير
            sim.df_enseignants = df_profs
            sim.df_salles = df_salles
            sim.df_classes = df_classes
            # (ملاحظة: المحرك سيقرأ ملف matieres_data.csv تلقائياً من المجلد)
            
            # 3. إعادة بناء الفهارس بالبيانات الجديدة
            sim.build_indexes()
            
            # 4. توليد الجداول الزمنية في الذاكرة الحية
            df_candidats = sim.generate_candidates(n=n_candidates, max_retries=300)
            
            # 5. استخراج أفضل 3 جداول بناءً على التقييم (Score)
            # نستخدم drop_duplicates للتأكد من الحصول على معرّفات مرشحين فريدة
            top_candidates = df_candidats[['Candidate_ID', 'Score']].drop_duplicates().sort_values(by='Score', ascending=False).head(3)
            
            st.success("✅ Génération terminée avec succès !")
            
            if top_candidates.empty:
                st.warning("⚠️ Aucun emploi du temps valide n'a pu être généré. Essayez d'augmenter le nombre de tentatives (max_retries) ou de vérifier vos contraintes.")
            else:
                # 6. عرض النتائج الحقيقية في التبويبات
                tabs = st.tabs(["🥇 Option 1", "🥈 Option 2", "🥉 Option 3"])
                
                for i, (index, row) in enumerate(top_candidates.iterrows()):
                    cand_id = row['Candidate_ID']
                    cand_score = row['Score']
                    
                    # استخراج الجدول الخاص بهذا المرشح فقط
                    df_emploi_final = df_candidats[df_candidats['Candidate_ID'] == cand_id]
                    
                    with tabs[i]:
                        st.metric(label="Score de Qualité", value=f"{cand_score}/100")
                        # عرض الجدول الحقيقي بشكل تفاعلي
                        st.dataframe(df_emploi_final, use_container_width=True, hide_index=True)
else:
    st.warning("⚠️ En attente des données. Le bouton de génération apparaîtra une fois les fichiers importés dans le menu à gauche.")