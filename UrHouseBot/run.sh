currentDir=$(cd $(dirname ${BASH_SOURCE[0]}); pwd)
cd $currentDir
cd ..
source ./venv/bin/activate
echo '激活虚拟环境 ------'

command -v scrapy > /dev/null || echo '安装依赖 ------' && pip install -r requirements.txt

cd $currentDir


file=log`date +"%Y-%m-%d_%H%M%S"`.log
runfile="$currentDir/run.py"

echo "后台运行 $(which python)"
nohup python $runfile > logs/$file 2>&1 &
ln -s -f logs/$file latest.log