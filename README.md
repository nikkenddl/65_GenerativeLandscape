# 65_GenerativeLandscape
Generative Designに利用するpythonライブラリ。ghファイルに含まれるghpythonコンポーネントからこのライブラリをロードして利用する。

ghファイル/必要なデータはリリース時にアップロード。

# How to Use
## Directory Struction
root

├── MapCreator_65.gh

├── ForestCreator_65.gh

└── lib_65land  <- this repository

anywhere
- forest_domain_data.xlsx
- tree_asset_table.xlsx
## Dependancies
- Net.SourceForge.Koogra
  - Excelを読み込むために利用。ghpythonから読める場所に配置する。
## Step
1. config.Configの"self.__path_forest_domain"と"self.__path_tree_asset"にそれぞれのExcelファイルのパスを記述する。
2. map_creator.ghで植栽帯に対する解析を行う。解析は任意の大きさのセルごとに実行され、MeshのUserTextに解析値をアーカイブする。encode/decodeの効率とファイルサイズを考慮して、リストの解析値をpickleでバイナリに変換し、それをbase64でテキストデータにする。
3. forest_creator.ghを開くと、1の情報を自動で読み取り配置が行われる。
