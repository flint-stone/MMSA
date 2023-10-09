from MMSA import MMSA_run, MMSA_test, get_config_regression
import sys


# run LMF on MOSI with default hyper parameters
# config = get_config_regression('lmf', 'mosi')
# MMSA_run('lmf', 'mosi',
#          config=config, 
#          seeds=[1111, 1112, 1113], gpu_ids=[1])

# MMSA_run('self_mm', 'mosei', seeds=[1111], gpu_ids=[1])
# MMSA_run('self_mm', 'mosei', seeds=[1111, 1112, 1113], gpu_ids=[1])

config = get_config_regression('self_mm', 'mosei')
config['batch_size'] = int(sys.argv[2])

MMSA_run('self_mm', 'mosei',
         config=config, 
         seeds=[1111], gpu_ids=[1],
         modality_skips_str=sys.argv[1],
         precision=sys.argv[3])

# MMSA_run('self_mm', 'mosei',
#          config=config, 
#          seeds=[1111, 1112, 1113], gpu_ids=[0])

# MMSA_test(config=config, 
#           weights_path = "/home/lexu/MMSA/saved_models/lmf-mosi.pth",
#           feature_path = "/home/lexu/MMSA/dataset/MOSEI/Processed/unaligned_50.pkl", 
#          gpu_id=1)


# config = get_config_regression('lmf', 'mosi')
# MMSA_test(config = config, 
#          weights_path = "/home/lexu/MMSA/saved_models/lmf-mosi.pth", 
#          feature_path = "/home/lexu/MMSA/dataset/MOSI/Processed/unaligned_50.pkl",
#          gpu_id=1)

# # tune Self_mm on MOSEI with default hyper parameter range
# MMSA_run('self_mm', 'mosei', seeds=[1111], gpu_ids=[1])

# # run TFN on SIMS with altered config
# config = get_config_regression('tfn', 'mosi')
# config['post_fusion_dim'] = 32
# config['featurePath'] = '~/feature.pkl'
# MMSA_run('tfn', 'mosi', config=config, seeds=[1111])

# # run MTFN on SIMS with custom config file
# MMSA_run('mtfn', 'sims', config_file='./config.json')