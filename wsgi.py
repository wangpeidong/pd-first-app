print(f"__file__={__file__:<35} | __name__={__name__:<20} | __package__={str(__package__):<20}")

from app.main import app

if __name__ == "__main__":
    app.run(debug = True)
    
print(f"---end of {__name__}---")    