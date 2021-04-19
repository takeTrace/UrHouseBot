currentDir="$(dirname $0)"
cd $currentDir
file=log`date +"%Y-%m-%d_%H%M%S"`.log
runfile="$currentDir/run.py"
nohup '/usr/local/Caskroom/miniconda/base/envs/scrapy/bin/python' $runfile > logs/$file 2>&1 &
ln -s -f logs/$file latest.log