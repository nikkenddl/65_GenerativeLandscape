data_species_property = """＜常緑針葉樹＞			
アカマツ
カヤ
モミ
＜常緑広葉樹＞
ライラック		
ホルトノキ
アラカシ
シラカシ
シロダモ
スダジイ
タブノキ
モッコク
カクレミノ
ネズミモチ
モチノキ
ヤブツバキ
ヤブニッケイ
ユズリハ
ソヨゴ
ハイノキ
ヤツデ
アセビ
ナンテン
マサキ
＜落葉広葉樹＞			
ケヤキ
ヤマザクラ
ウワミズザクラ
イヌザクラ
カスミザクラ
エノキ
コナラ
クヌギ
コブシ
アオハダ
カツラ
アオダモ
アカシデ
ミズキ
イヌシデ
イロハモミジ
エゴノキ
ヤマボウシ			
YB1	8.0	株立	3.5
YB2	5.0	株立	2.5
YB3	3.0	株立	1.5
ホオノキ			
HO	8.0	株立	3.5
サルスベリ			
SA	5.5	株立	3.5
ハンノキ			
HK1	5.0	株立	2.0
HK2	3.0	株立	1.0
ミツバツツジ			
MT	3.0	株立	1.5
ヤマツツジ			
YJ	2.0	株立	1.2
ウグイスカグラ			
UK	2.0	株立	1.0
オトコヨウゾメ			
OY	2.0	株立	1.0
クロモジ			
KJ	2.0	株立	1.0
ツリバナ			
TR	2.0	株立	1.5
ヤブデマリ			
YD	2.0	株立	1.2
ダンコウバイ			
DB	2.0	株立	1.0
ニシキギ			
NG	2.0	株立	1.2
マユミ			
MY	2.0	株立	1.0
ガマズミ			
GZ	2.0	株立	1.2
サンショウ			
SS	2.0	株立	1.0
リョウブ			
RB	2.0	株立	1.0
ライラック			
RR	2.0	株立	1.2"""

data_species = """アオダモ
アオハダ
アカシデ
アカマツ
アセビ
アラカシ
イヌザクラ
イヌシデ
イロハモミジ
ウグイスカグラ
ウワミズザクラ
エゴノキ
エノキ
オトコヨウゾメ
カクレミノ
カスミザクラ
カツラ
ガマズミ
カヤ
クヌギ
クロモジ
ケヤキ
コナラ
コブシ
サルスベリ
サンショウ
シラカシ
シロダモ
スダジイ
ソヨゴ
タブノキ
ダンコウバイ
ツリバナ
ナンテン
ニシキギ
ネズミモチ
ハイノキ
ハンノキ
ホオノキ
ホルトノキ
マサキ
マユミ
ミズキ
ミツバツツジ
モチノキ
モッコク
モミ
ヤツデ
ヤブツバキ
ヤブデマリ
ヤブニッケイ
ヤマザクラ
ヤマツツジ
ヤマボウシ
ユズリハ
ライラック
リョウブ
"""

from pprint import pprint
import re

EVERGREEN_TEXT = "常緑"
DICIDOUS_TEXT = "落葉"
BROADLEAF_TEXT = "広葉"
CONIFERS_TEXT = "針葉"



if __name__=='__main__':
    data_list = [t.strip() for t in data_species_property.split("\n")]
    data_list = [t for t in data_list if t]
    # remove symbol rows
    pat = re.compile(r"[a-zA-Z\s\.\,]+")
    data_list = list(filter(lambda t: t and not pat.match(t), data_list))

    # split with category
    keys = (EVERGREEN_TEXT,DICIDOUS_TEXT,BROADLEAF_TEXT,CONIFERS_TEXT)
    pat_string = "{}".format("|".join(t for t in keys))
    print(pat_string)
    pat = re.compile(pat_string)
    key_indices = []

    for i,row in enumerate(data_list):
        if pat.search(row):
            # check category contains is_evergreen and is_broadleaf
            if not (
                (EVERGREEN_TEXT in row or DICIDOUS_TEXT in row)
            and (BROADLEAF_TEXT in row or CONIFERS_TEXT in row)
            ):
                raise Exception(f"Can't recognise category property from row:{row}")
            key_indices.append(i)
    
    if not key_indices: raise Exception("No category is found")
    
    key_indices.append(-1)
    categorized_data = {}
    for si,ei in zip(key_indices[:-1],key_indices[1:]):
        categorized_data[data_list[si]] = data_list[si+1:ei]

    # make species dictionary whose species is is_evergreen and is_conifers
    category_dict = {} #species: (is_evergreen,is_conifers)
    for category,species_list in categorized_data.items():
        is_evergreen = EVERGREEN_TEXT in category
        is_conifers = CONIFERS_TEXT in category
        for species in species_list:
            category_dict[species] = (is_evergreen,is_conifers)

    # make species properties list by category_dict
    speacies_list = [t.strip() for t in data_species.split("\n")]
    speacies_list = [t for t in speacies_list if t]
    print('is_evergreen------------------------')
    print('\n'.join("TRUE" if category_dict[s][0] else "FALSE" for s in speacies_list))

    
    print('\n\nis_conifers------------------------')
    print('\n'.join("TRUE" if category_dict[s][1] else "FALSE" for s in speacies_list))