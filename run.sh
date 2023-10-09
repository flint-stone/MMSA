#!/bin/bash

python -m pip uninstall -y MMSA
python -m pip install .

# python run.py "text" 32
PRECISION="fp32" #"fp16" #"fp32"

# #!/bin/bash

# python run.py "text" 1 $PRECISION

# for (( BATCH=1; BATCH<=32; BATCH++ ))
# do
#     for DROP in "None" "text" "audio" "vision" "text,audio" "audio,vision" "text,vision"
#     do
#         python run.py $DROP $BATCH $PRECISION 2>&1 >output-${PRECISION}/batch${BATCH}-${DROP}.log

#     done
# done


python run.py None 32 $PRECISION > $PRECISION-out.log