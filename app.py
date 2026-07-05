import os
from static.wtf import app

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5500"))
    app.run(debug=True, port=port)
