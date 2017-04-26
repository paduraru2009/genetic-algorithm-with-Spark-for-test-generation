echo "Run Spark..."
// CPADURARU FIX PATH
sh ~/Downloads/spark-2.0.1-bin-hadoop2.7/bin/spark-submit \
           --master spark://yosemite:7077 \
           --num-executors 2 \
           --total-executor-cores 2 \
           --executor-memory 1g \
           main.py 

echo ""
echo "Done."

