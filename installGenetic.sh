
CLEAN_BUILD=$1
WRITE_IN_BASHRC=$2

GENETIC="genetic"
BLUE='\033[0;34m'
NC='\033[0m' # No Color

if [ "$CLEAN_BUILD" = "clean"  ]; then
printf "${BLUE}Step 1: installing Python packages\n${NC}"

sudo apt-get install -y python3-pip git
pip3 --no-cache-dir install pyspark==2.4.3
pip3 install parse==1.12.0

printf "${BLUE}Step 2: installing Java\n${NC}"

sudo apt-get install -y openjdk-8-jdk

printf "${BLUE}Step 3: Clone Github repository\n${NC}"
if [ -d "$GENETIC" ]; then rm -rf $GENETIC; fi
mkdir $GENETIC
cd $GENETIC

git clone https://github.com/paduraru2009/genetic-algorithm-with-Spark-for-test-generation.git 

# Remove unused files
cd genetic-algorithm-with-Spark-for-test-generation/
find ./ -name .gitkeep -delete

cd ~/
fi

if [ "$WRITE_IN_BASHRC" = "bashrc"  ]; then
printf "${BLUE}Step 4: Add enviroment variables\n${NC}"

echo "export SIMPLETRACERPATH=/usr/local/bin/river.tracer" >> ~/.bashrc
echo "export SIMPLETRACERLOGSPATH=$PWD/logs" >> ~/.bashrc
fi
