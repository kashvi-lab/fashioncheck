
import streamlit as st
import anthropic

# ── Page config ────────────────────────────────────────────────
st.set_page_config(
    page_title="FashionCheck — AI Pre-Validation Platform",
    page_icon="✦",
    layout="wide"
)

# ── Lookup tables ──────────────────────────────────────────────
FIBRE_SCORES = {
    "Deadstock / upcycled": 10,
    "Organic cotton (GOTS)": 9,
    "Recycled polyester": 8,
    "Recycled wool": 8,
    "Linen / hemp / flax": 8,
    "TENCEL / Lyocell": 7,
    "Conventional cotton": 5,
    "Wool (virgin)": 5,
    "Standard viscose": 3,
    "Virgin polyester": 2,
    "Virgin nylon": 2,
    "Acrylic": 1,
    "PVC / PU coated": 1,
}

CATEGORY_COMPLEXITY = {
    "Accessories / bags": 9,
    "Jersey tops / tees": 8,
    "Knitwear": 8,
    "Skirts": 8,
    "Denim": 6,
    "Dresses": 6,
    "Trousers": 5,
    "Outerwear": 4,
    "Swimwear": 3,
    "Tailoring / blazers": 3,
    "Occasionwear": 2,
}

CERT_POINTS = {
    "GOTS (Global Organic Textile Standard)": 4,
    "Cradle to Cradle": 3,
    "Global Recycled Standard (GRS)": 3,
    "Oeko-Tex Standard 100": 2,
    "Fair Trade certified": 2,
    "BCI (Better Cotton Initiative)": 2,
    "RWS (Responsible Wool Standard)": 2,
    "EU Ecolabel": 2,
}

# ── Scoring engine ─────────────────────────────────────────────
def calculate_blended_fibre_score(fibres):
    """
    fibres = list of (fibre_name, percentage) tuples
    Returns weighted average score based on composition
    """
    total_pct = sum(pct for _, pct in fibres)
    if total_pct == 0:
        return 0
    score = sum(
        FIBRE_SCORES.get(name, 5) * (pct / total_pct)
        for name, pct in fibres
    )
    return round(score, 1)

def calculate_cert_score(selected_certs):
    """Cumulative cert score, capped at 10"""
    total = sum(CERT_POINTS.get(c, 0) for c in selected_certs)
    return min(round((total / 10) * 10, 1), 10)

def calculate_sustainability_score(fibre_score, supplier_rating,
                                    cert_score, complexity_score):
    weights = {
        "fibre": 0.30, "supplier": 0.25,
        "cert": 0.25, "complexity": 0.20
    }
    raw = (fibre_score    * weights["fibre"]      +
           supplier_rating * weights["supplier"]   +
           cert_score      * weights["cert"]        +
           complexity_score * weights["complexity"])
    return round(raw * 10, 1)

def calculate_compliance_score(espr, dpp, cma, eol):
    weights = {"espr": 0.35, "dpp": 0.30, "cma": 0.20, "eol": 0.15}
    raw = (espr * weights["espr"] + dpp * weights["dpp"] +
           cma  * weights["cma"]  + eol * weights["eol"])
    return round(raw * 10, 1)

def get_verdict(s_score, c_score):
    avg = (s_score + c_score) / 2
    if avg >= 70:
        return "APPROVED — proceed to sampling", "green"
    elif avg >= 50:
        return "PROCEED WITH IMPROVEMENTS", "orange"
    else:
        return "FLAGGED — significant issues", "red"

# ── AI suggestions ─────────────────────────────────────────────
def get_ai_suggestions(product_name, category, fibres, supplier_rating,
                        selected_certs, espr, dpp, cma, eol,
                        s_score, c_score, api_key):

    fibre_breakdown = ", ".join(
        f"{pct}% {name}" for name, pct in fibres if pct > 0
    )
    cert_list = ", ".join(selected_certs) if selected_certs else "None"

    client = anthropic.Anthropic(api_key=api_key)
    prompt = f"""
You are an expert sustainability consultant advising a UK fashion SME founder.
Be practical, specific and supportive — not academic or preachy.

Product: {product_name}
Category: {category}
Fibre composition: {fibre_breakdown}
Supplier region score: {supplier_rating}/10
Certifications held: {cert_list}
ESPR alignment (durable/repairable): {"Yes" if espr == 8 else "No"}
DPP data readiness (supply chain data): {"Yes" if dpp == 8 else "No"}
CMA green claims substantiated: {"Yes" if cma == 8 else "No"}
End-of-life recyclable/compostable: {"Yes" if eol == 8 else "No"}

Sustainability score: {s_score}/100
Compliance score: {c_score}/100

Identify the 3 weakest areas and for each provide:
1. The specific problem in one sentence
2. A concrete material or process alternative (name it specifically)
3. A named certification to pursue with a brief note on what it covers
4. Regulatory urgency — name the specific regulation and deadline
5. Honest cost impact — one sentence estimate

Then end with:
PARTNER TYPES: 2-3 types of suppliers or organisations an SME could work with
RISK NOTE: One sentence on the biggest risk of proceeding unchanged.

Format exactly like this:

SUGGESTION 1: [factor name]
Problem: [one sentence]
Alternative: [specific material or process swap]
Certification: [name] — [what it covers]
Regulation: [specific rule and deadline]
Cost impact: [honest estimate]

SUGGESTION 2: [factor name]
Problem: [one sentence]
Alternative: [specific material or process swap]
Certification: [name] — [what it covers]
Regulation: [specific rule and deadline]
Cost impact: [honest estimate]

SUGGESTION 3: [factor name]
Problem: [one sentence]
Alternative: [specific material or process swap]
Certification: [name] — [what it covers]
Regulation: [specific rule and deadline]
Cost impact: [honest estimate]

PARTNER TYPES: [2-3 specific partner types]
RISK NOTE: [one sentence]
"""
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=800,
        messages=[{"role": "user", "content": prompt}]
    )
    return message.content[0].text

# ── Sidebar ────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ✦ FashionCheck")
    st.markdown("*AI Pre-Validation Platform for UK Fashion SMEs*")
    st.divider()

    api_key = st.secrets["ANTHROPIC_API_KEY"]

    st.divider()
    st.markdown("**About this tool**")
    st.markdown(
        "FashionCheck scores your product concept against UK and EU "
        "sustainability and compliance standards before you commit to sampling."
    )
    st.markdown("Built for UK fashion SMEs · Degree project · Kashvi Soni")

# ── Main panel ─────────────────────────────────────────────────
st.title("Product Pre-Validation")
st.markdown(
    "Enter your product concept below. "
    "The system scores it against UK and EU sustainability "
    "and compliance standards automatically."
)
st.divider()

# ── Section 1: Product basics ──────────────────────────────────
st.markdown("### Product basics")

col1, col2 = st.columns(2)
with col1:
    product_name = st.text_input(
        "Product name",
        placeholder="e.g. Recycled Denim Jacket"
    )
with col2:
    category = st.selectbox(
        "Product category",
        options=list(CATEGORY_COMPLEXITY.keys())
    )

complexity_score = CATEGORY_COMPLEXITY[category]

st.divider()

# ── Section 2: Fibre composition ───────────────────────────────
st.markdown("### Fibre composition")
st.markdown("*Add up to 3 fibres — percentages must total 100%*")

fibre_options = ["— select —"] + list(FIBRE_SCORES.keys())

fc1, fc2, fc3 = st.columns(3)

with fc1:
    fibre1 = st.selectbox("Fibre 1", fibre_options, key="f1")
    pct1 = st.number_input("% share", 0, 100, 100,
                            key="p1", step=5)

with fc2:
    fibre2 = st.selectbox("Fibre 2", fibre_options, key="f2")
    pct2 = st.number_input("% share", 0, 100, 0,
                            key="p2", step=5)

with fc3:
    fibre3 = st.selectbox("Fibre 3", fibre_options, key="f3")
    pct3 = st.number_input("% share", 0, 100, 0,
                            key="p3", step=5)

# Build fibre list and validate
fibres = []
if fibre1 != "— select —" and pct1 > 0:
    fibres.append((fibre1, pct1))
if fibre2 != "— select —" and pct2 > 0:
    fibres.append((fibre2, pct2))
if fibre3 != "— select —" and pct3 > 0:
    fibres.append((fibre3, pct3))

total_pct = sum(pct for _, pct in fibres)

if total_pct != 100 and len(fibres) > 0:
    st.warning(f"Fibre percentages total {total_pct}% — they must add up to 100%")
elif len(fibres) > 0:
    st.success(f"Fibre composition confirmed — {total_pct}% accounted for")

fibre_score = calculate_blended_fibre_score(fibres) if total_pct == 100 else 0

st.divider()

# ── Section 3: Supplier & certifications ───────────────────────
st.markdown("### Supplier & certifications")

sup_col, cert_col = st.columns(2)

with sup_col:
    supplier_options = {
        "UK / local manufacturer": 10,
        "Europe (EU or EEA)": 8,
        "Turkey or North Africa": 6,
        "South Asia — audited supplier (Bangladesh, India, Pakistan)": 4,
        "South Asia — no audit or traceability": 2,
        "High risk region — no data available": 1,
    }
    supplier_choice = st.selectbox(
        "Supplier region",
        options=list(supplier_options.keys()),
        help="Select the region where your product is manufactured"
    )
    supplier_rating = supplier_options[supplier_choice]
    st.caption(f"Score assigned: {supplier_rating} / 10")

with cert_col:
    selected_certs = st.multiselect(
        "Certifications held",
        options=list(CERT_POINTS.keys()),
        help="Select all that apply"
    )

cert_score = calculate_cert_score(selected_certs)

st.divider()

# ── Section 4: Compliance questions ────────────────────────────
st.markdown("### Compliance readiness")
st.markdown("*Answer honestly — these map directly to UK and EU regulatory requirements*")

q_col1, q_col2 = st.columns(2)

with q_col1:
    espr_ans = st.radio(
        "Is this product designed to be durable and repairable?",
        ["Yes", "No"],
        horizontal=True,
        help="ESPR ecodesign regulation — mandatory for EU market from 2027"
    )
    dpp_ans = st.radio(
        "Do you have full supply chain data available?",
        ["Yes", "No"],
        horizontal=True,
        help="Required for Digital Product Passports — mandatory from 2030"
    )

with q_col2:
    cma_ans = st.radio(
        "Are all your sustainability claims substantiated with evidence?",
        ["Yes", "No"],
        horizontal=True,
        help="UK CMA green claims code — enforceable now"
    )
    eol_ans = st.radio(
        "Can this product be recycled or composted at end of life?",
        ["Yes", "No"],
        horizontal=True,
        help="EU Waste Framework Directive extended producer responsibility"
    )

# Convert answers to scores
espr = 8 if espr_ans == "Yes" else 2
dpp  = 8 if dpp_ans  == "Yes" else 2
cma  = 8 if cma_ans  == "Yes" else 2
eol  = 8 if eol_ans  == "Yes" else 2

st.divider()

# ── Live scores ────────────────────────────────────────────────
st.markdown("### Your scores")

if total_pct != 100 or len(fibres) == 0:
    st.info("Complete the fibre composition above to see your scores.")
else:
    s_score = calculate_sustainability_score(
        fibre_score, supplier_rating, cert_score, complexity_score
    )
    c_score = calculate_compliance_score(espr, dpp, cma, eol)
    verdict, colour = get_verdict(s_score, c_score)

    m1, m2, m3 = st.columns(3)
    with m1:
        st.metric("Sustainability score", f"{s_score} / 100")
    with m2:
        st.metric("Compliance score", f"{c_score} / 100")
    with m3:
        st.metric("Overall average", f"{round((s_score + c_score) / 2, 1)} / 100")

    if colour == "green":
        st.success(f"✦ {verdict}")
    elif colour == "orange":
        st.warning(f"⚠ {verdict}")
    else:
        st.error(f"✕ {verdict}")

    # Score breakdown
    with st.expander("See score breakdown"):
        b1, b2, b3, b4 = st.columns(4)
        with b1:
            st.metric("Fibre score", f"{fibre_score} / 10")
        with b2:
            st.metric("Supplier score", f"{supplier_rating} / 10")
        with b3:
            st.metric("Cert score", f"{cert_score} / 10")
        with b4:
            st.metric("Complexity score", f"{complexity_score} / 10")

    st.divider()

    # ── AI suggestions ─────────────────────────────────────────
    st.markdown("### AI improvement suggestions")

    if not api_key:
        st.info("Enter your Anthropic API key in the sidebar to generate suggestions.")
    elif not product_name:
        st.info("Enter a product name above to generate suggestions.")
    else:
        if st.button("Generate AI suggestions", type="primary"):
            with st.spinner("Analysing your concept and generating suggestions..."):
                suggestions = get_ai_suggestions(
                    product_name, category, fibres,
                    supplier_rating, selected_certs,
                    espr, dpp, cma, eol,
                    s_score, c_score, api_key
                )

            sections = suggestions.strip().split("\n\n")
            for section in sections:
                if section.startswith("SUGGESTION"):
                    lines = section.strip().split("\n")
                    title = lines[0]
                    with st.expander(title, expanded=True):
                        for line in lines[1:]:
                            if line.startswith("Problem:"):
                                st.markdown(f"**Problem:** {line.replace('Problem:', '').strip()}")
                            elif line.startswith("Alternative:"):
                                st.markdown(f"**Alternative:** {line.replace('Alternative:', '').strip()}")
                            elif line.startswith("Certification:"):
                                st.markdown(f"**Certification:** {line.replace('Certification:', '').strip()}")
                            elif line.startswith("Regulation:"):
                                st.markdown(f"**Regulation:** {line.replace('Regulation:', '').strip()}")
                            elif line.startswith("Cost impact:"):
                                st.markdown(f"**Cost impact:** {line.replace('Cost impact:', '').strip()}")
                elif section.startswith("PARTNER TYPES:"):
                    st.markdown("**Recommended partner types**")
                    st.info(section.replace("PARTNER TYPES:", "").strip())
                elif section.startswith("RISK NOTE:"):
                    st.markdown("**Risk of proceeding unchanged**")
                    st.error(section.replace("RISK NOTE:", "").strip())

