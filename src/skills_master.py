# skills_master.py

# === Global Skill Dictionary ===
SKILLS = {
    # --- Core Programming Languages ---
    "python": 1.3, "java": 1.3, "c++": 1.3, "c#": 1.2, "golang": 1.2,
    "php": 1.1, "ruby": 1.1, "typescript": 1.2, "javascript": 1.2,
    "kotlin": 1.2, "swift": 1.2, "r": 1.1, "matlab": 1.1, "rust": 1.2,
    "scala": 1.2, "perl": 1.0, "lua": 1.0, "dart": 1.2,

    # --- Developer Roles ---
    "frontend developer": 1.3, "backend developer": 1.3,
    "full stack developer": 1.3, "mobile developer": 1.3,
    "android developer": 1.3, "ios developer": 1.3,
    "flutter developer": 1.3, "react native developer": 1.3,
    "game developer": 1.3, "unity developer": 1.2, "unreal developer": 1.2,
    "ai engineer": 1.3, "ml engineer": 1.3, "data engineer": 1.3,
    "data scientist": 1.3, "data analyst": 1.3,
    "devops engineer": 1.3, "cloud engineer": 1.3,
    "cybersecurity engineer": 1.3, "blockchain developer": 1.3,
    "web developer": 1.2, "software developer": 1.3,
    "embedded systems developer": 1.3, "firmware engineer": 1.2,
    "ar/vr developer": 1.3, "ui developer": 1.2,
    "qa engineer": 1.2, "test automation engineer": 1.2,

    # --- Frameworks & Libraries (Frontend) ---
    "react": 1.3, "vue": 1.2, "angular": 1.2, "next.js": 1.2, "nuxt.js": 1.1,
    "svelte": 1.1, "solidjs": 1.0, "astro": 1.0,
    "html": 1.1, "css": 1.1, "bootstrap": 1.1, "tailwind": 1.1,
    "sass": 1.1, "less": 1.0,

    # --- Backend Frameworks ---
    "node.js": 1.3, "express": 1.2, "nestjs": 1.2,
    "django": 1.3, "flask": 1.2, "fastapi": 1.3,
    "spring boot": 1.3, "spring": 1.2, "laravel": 1.2, "codeigniter": 1.1,
    "dotnet": 1.2, "asp.net": 1.2, "rails": 1.1, "phoenix": 1.0,
    "gin": 1.1, "fiber": 1.1,

    # --- Mobile Frameworks ---
    "flutter": 1.3, "react native": 1.3, "swiftui": 1.1,
    "jetpack compose": 1.1, "xamarin": 1.0, "ionic": 1.0, "cordova": 1.0,

    # --- Game Engines ---
    "unity": 1.3, "unreal engine": 1.3, "godot": 1.1, "cryengine": 1.0,

    # --- Databases ---
    "sql": 1.2, "mysql": 1.2, "postgresql": 1.2, "sqlite": 1.1, "oracle": 1.1,
    "mongodb": 1.2, "firebase": 1.1, "redis": 1.1, "cassandra": 1.1,
    "dynamodb": 1.1, "elasticsearch": 1.1, "snowflake": 1.1,

    # --- DevOps & Cloud ---
    "devops": 1.3, "ci/cd": 1.3, "docker": 1.3, "kubernetes": 1.3,
    "jenkins": 1.2, "terraform": 1.2, "ansible": 1.1, "github actions": 1.1,
    "aws": 1.3, "azure": 1.3, "gcp": 1.3, "digitalocean": 1.0,
    "linux": 1.2, "nginx": 1.1, "apache": 1.1,

    # --- AI / ML / Data ---
    "ai": 1.3, "ml": 1.3, "deep learning": 1.3, "nlp": 1.3, "computer vision": 1.3,
    "data science": 1.3, "data analysis": 1.3, "data engineering": 1.3,
    "chatgpt": 1.2, "llm": 1.2, "rag": 1.1,
    "pandas": 1.1, "numpy": 1.1, "scikit-learn": 1.1, "tensorflow": 1.2,
    "pytorch": 1.2, "matplotlib": 1.1, "seaborn": 1.1, "huggingface": 1.1,
    "openai api": 1.2, "langchain": 1.2, "mlflow": 1.0, "keras": 1.1,
    "spark": 1.1, "hadoop": 1.1, "big data": 1.2,

    # --- Blockchain & Web3 ---
    "blockchain": 1.3, "solidity": 1.2, "ethereum": 1.2, "web3.js": 1.1,
    "truffle": 1.0, "hardhat": 1.0, "rust (solana)": 1.1,

    # --- AR/VR / 3D ---
    "unity3d": 1.2, "three.js": 1.1, "blender": 1.1, "oculus sdk": 1.0,
    "arcore": 1.0, "arkit": 1.0, "xr": 1.0,

    # --- Security ---
    "cybersecurity": 1.3, "ethical hacking": 1.3,
    "penetration testing": 1.3, "network security": 1.2,
    "cryptography": 1.2, "forensics": 1.1, "firewalls": 1.1,

    # --- QA & Testing ---
    "sqa": 1.3, "quality assurance": 1.3,
    "manual testing": 1.2, "automation testing": 1.2,
    "selenium": 1.2, "junit": 1.1, "pytest": 1.1, "testng": 1.1,
    "api testing": 1.2, "load testing": 1.1, "cypress": 1.1, "playwright": 1.1,

    # --- Miscellaneous Tech ---
    "rest api": 1.2, "graphql": 1.1, "grpc": 1.1,
    "microservices": 1.2, "message queues": 1.1, "rabbitmq": 1.1, "kafka": 1.1,
    "websockets": 1.1, "oauth": 1.1,

    # --- System, Hardware & Embedded ---
    "embedded systems": 1.3, "arduino": 1.2, "raspberry pi": 1.2,
    "firmware": 1.2, "rtos": 1.1, "iot": 1.3, "edge computing": 1.1,

    # --- Management & Business ---
    "project manager": 1.3, "scrum master": 1.2,
    "product manager": 1.3, "system analyst": 1.2,
    "business analyst": 1.2, "software architect": 1.3, "tech lead": 1.2,
    "consultant": 1.2, "it consultant": 1.2,
    "entrepreneurship": 1.3, "leadership": 1.2,

    # --- UI/UX & Design ---
    "ui/ux": 1.2, "figma": 1.1, "adobe xd": 1.0, "photoshop": 1.0,
    "illustrator": 1.0, "wireframing": 1.0, "prototyping": 1.0,
}

# === Context-Aware Skill Mapping ===
# Helps map variations like "NestJS Framework" -> "nestjs"
SKILL_CONTEXT_MAP = {
    # --- Frameworks & Libraries ---
    "nestjs": ["nest.js", "nestjs framework"],
    "laravel": ["laravel framework"],
    "flutter": ["flutter framework", "dart ui"],
    "react native": ["reactnative", "react-native"],
    "spring boot": ["springboot"],
    "unity": ["unity3d", "unity engine"],
    "unreal engine": ["unrealengine", "ue4", "ue5"],
    "fastapi": ["python api framework"],
    "next.js": ["nextjs"], "nuxt.js": ["nuxtjs"],
    "tailwind": ["tailwindcss"], "bootstrap": ["bootstrap5", "bootstrap4"],

    # --- Mobile ---
    "jetpack compose": ["android compose"],
    "swiftui": ["ios ui", "swift ui"],
    "xamarin": ["xamarin forms"], "ionic": ["ionic framework"],

    # --- Data / ML ---
    "huggingface": ["transformers", "hf"],
    "langchain": ["llm orchestration", "ai pipeline"],
    "mlflow": ["ml ops", "mlops"],
    "keras": ["deep learning library"],

    # --- DevOps ---
    "github actions": ["gh actions"],
    "nginx": ["reverse proxy"], "apache": ["apache server"],

    # --- Blockchain ---
    "solidity": ["smart contracts"],
    "web3.js": ["web3"], "truffle": ["truffle suite"],
    "hardhat": ["smart contract testing"],

    # --- Testing ---
    "cypress": ["end-to-end testing", "e2e"],
    "playwright": ["browser automation"],

    # --- Embedded / IoT ---
    "arduino": ["microcontroller", "atmega"],
    "raspberry pi": ["raspi", "pi board"],
    "iot": ["internet of things"], "rtos": ["real-time os"],

    # --- Developer Roles ---
    "frontend developer": ["frontend dev", "ui developer"],
    "backend developer": ["backend dev", "server-side developer"],
    "full stack developer": ["fullstack developer", "full-stack dev"],
    "mobile developer": ["mobile app developer", "app developer"],
    "android developer": ["android dev", "kotlin developer"],
    "ios developer": ["ios dev", "swift developer"],
    "flutter developer": ["flutter dev"],
    "react native developer": ["rn developer"],
    "game developer": ["game dev", "game programmer"],
    "ai engineer": ["artificial intelligence engineer"],
    "ml engineer": ["machine learning engineer"],
    "data engineer": ["etl engineer"],
    "devops engineer": ["devops specialist", "cloud devops"],
    "cloud engineer": ["cloud specialist", "cloud architect"],
    "blockchain developer": ["smart contract developer"],
    "qa engineer": ["qa tester", "sqa engineer"],
    "embedded systems developer": ["embedded developer"],
    "ar/vr developer": ["xr developer", "metaverse developer"],
}