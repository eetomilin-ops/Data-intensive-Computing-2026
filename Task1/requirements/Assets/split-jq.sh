jq -c 'select((input_line_number-1)%4==0)' reviews_devset.json > part_1.json
jq -c 'select((input_line_number-1)%4==1)' reviews_devset.json > part_2.json
jq -c 'select((input_line_number-1)%4==2)' reviews_devset.json > part_3.json
jq -c 'select((input_line_number-1)%4==3)' reviews_devset.json > part_4.json