# 65_GenerativeLandscape
Generative Designに利用するpythonライブラリをまとめる。
ghファイルに含まれるghpythonコンポーネントからこのライブラリをロードする。
ghファイルはリリース時にアップロード。

# How to Use
## Directory Struction
root

├── MapCreator_65.gh

├── ForestCreator_65.gh

└── lib_65land  <- this repository

## Step
1. map_creator.ghで植栽帯に対する解析を行う。解析は任意の大きさのセルごとに実行され、MeshのUserTextに解析値をアーカイブする。encode/decodeの効率とファイルサイズを考慮して、リストの解析値をpickleでバイナリに変換し、それをbase64でテキストデータにする。
2. forest_creator.ghを開くと、1の情報を自動で読み取り配置が行われる。
