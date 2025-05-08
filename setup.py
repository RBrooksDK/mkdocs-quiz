from distutils.core import setup

setup(
    name='mkdocs_quiz',
    version='0.0.43',
    packages=['mkdocs_quiz',],
    package_data={'mkdocs_quiz': ['css/*', 'js/*']},
    include_package_data=True,
    license='Apache License 2.0',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/RBrooksDK/mkdocs-quiz',
    description='A MkDocs plugin to create a quiz in your markdown document.',
    author='Richard Brooks',
    author_email='rib@via.dk',
    install_requires=[
        "mkdocs",
    ],
    entry_points={
        'mkdocs.plugins': [
            'mkdocs_quiz = mkdocs_quiz.plugin:MkDocsQuizPlugin'
        ]
    }
)
