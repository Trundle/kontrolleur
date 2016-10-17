from setuptools import setup

setup(
    name="kontrolleur",
    version="0.1.0",
    author="Andreas Stührk",
    author_email="andy@hammerhartes.de",
    install_requires=[
        "attrs",
        "curtsies",
    ],
    py_modules=["kontrolleur"],
    entry_points="""\
    [console_scripts]
    kontrolleur = kontrolleur:main
    """
)
