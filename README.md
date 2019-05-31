### Installing
    Must have RIVER and Simpletracer already installed (more info: https://github.com/AGAPIA/river)

    cd ~/
    wget https://raw.githubusercontent.com/paduraru2009/genetic-algorithm-with-Spark-for-test-generation/master/installGenetic.sh
    sh installGenetic.sh clean bashrc

    Restart terminal and test
        cd ~/genetic/genetic-algorithm-with-Spark-for-test-generation/

### Testing

    $ python3 main.py --logsPath $SIMPLETRACERLOGSPATH   # Running locally
    $ sh ./test.sh                                       # Running on Spark

### Viewing status while running

    $ python3 status.py $SIMPLETRACERLOGSPATH

### Viewing binary files that crashed

    $ python3 status_logs.py $SIMPLETRACERLOGSPATH

### Run on Spark with dummy data 

    $ ./run_example
     
### Run probabilities 

    $ python probabilities.py 


