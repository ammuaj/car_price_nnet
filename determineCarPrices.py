from NeuralNetworkTorch import *
import argparse
import pandas as pd

def confusion_matrix(Y_classes, T):
    class_names = np.unique(T)
    table = []

    for true_class in class_names:
        row = []
        for Y_class in class_names:
            row.append(100 * np.mean(Y_classes[T == true_class] == Y_class))
        table.append(row)
    conf_matrix = pandas.DataFrame(table, index=class_names, columns=class_names)
    # cf.style.background_gradient(cmap='Blues').format("{:.1f} %")
        
    return conf_matrix.style.background_gradient(cmap='Blues').format("{:.1f}")
    

def percent_correct(Y, T):
    return np.mean(Y == T) * 100

def partition(X, T, fractions=(0.6, 0.2, 0.2), shuffle=True, classification=False):
    """Usage: Xtrain,Train,Xvalidate,Tvalidate,Xtest,Ttest = partition(X,T,(0.6,0.2,0.2),classification=True)
      X is nSamples x nFeatures.
      fractions can have just two values, for partitioning into train and test only
      If classification=True, T is target class as integer. Data partitioned
        according to class proportions.
        """
    train_fraction = fractions[0]
    if len(fractions) == 2:
        # Skip the validation step
        validate_fraction = 0
        test_fraction = fractions[1]
    else:
        validate_fraction = fractions[1]
        test_fraction = fractions[2]
        
    row_indices = np.arange(X.shape[0])
    if shuffle:
        np.random.shuffle(row_indices)
    
    if not classification:
        # regression, so do not partition according to targets.
        n = X.shape[0]
        n_train = round(train_fraction * n)
        n_validate = round(validate_fraction * n)
        n_test = round(test_fraction * n)
        if n_train + n_validate + n_test > n:
            n_test = n - n_train - n_validate
        Xtrain = X[row_indices[:n_train], :]
        Ttrain = T[row_indices[:n_train], :]
        if n_validate > 0:
            Xvalidate = X[row_indices[n_train:n_train + n_validate], :]
            Tvalidate = T[row_indices[n_train:n_train + n_validate], :]
        Xtest = X[row_indices[n_train + n_validate:n_train + n_validate + n_test], :]
        Ttest = T[row_indices[n_train + n_validate:n_train + n_validate + n_test], :]
        
    else:
        # classifying, so partition data according to target class
        classes = np.unique(T)
        train_indices = []
        validate_indices = []
        test_indices = []
        for c in classes:
            # row indices for class c
            rows_this_class = np.where(T[row_indices,:] == c)[0]
            # collect row indices for class c for each partition
            n = len(rows_this_class)
            n_train = round(train_fraction * n)
            n_validate = round(validate_fraction * n)
            n_test = round(test_fraction * n)
            if n_train + n_validate + n_test > n:
                n_test = n - n_train - n_validate
            train_indices += row_indices[rows_this_class[:n_train]].tolist()
            if n_validate > 0:
                validate_indices += row_indices[rows_this_class[n_train:n_train + n_validate]].tolist()
            test_indices += row_indices[rows_this_class[n_train + n_validate:n_train + n_validate + n_test]].tolist()
        Xtrain = X[train_indices, :]
        Ttrain = T[train_indices, :]
        if n_validate > 0:
            Xvalidate = X[validate_indices, :]
            Tvalidate = T[validate_indices, :]
        Xtest = X[test_indices, :]
        Ttest = T[test_indices, :]
    if n_validate > 0:
        return Xtrain, Ttrain, Xvalidate, Tvalidate, Xtest, Ttest
    else:
        return Xtrain, Ttrain, Xtest, Ttest

def createArgParser():
    parser = argparse.ArgumentParser(description="Program that parses used car data csv file and trains a neural network to determine car price")
    
    parser.add_argument('input_csv', action="store", type=str, 
                        help="provide path the csv file that contains all the used car data.")

    parser.add_argument("-hu", "--hidden_units", action="store", type=str,
                        default=[10, 10], help="Provide list of hiddne units ej [10, 10] default is [10,10].")

    parser.add_argument("-v", "--verbose", action="store_true", default=False, help="increase output verbosity")

    parser.add_argument("-in", "--nn_inputs", action="store", type=str, 
                        help="list containing all the inputs wanted to be used in training pytorch nerual network")

    parser.add_argument("-out", "--nn_outputs", action="store", type=str, required=True,
                        help="list containing all the outputs wanted to be used in training pytorch nerual network")

    return parser

def createPandasDataFrame(args):
    car_data_df = None
    if(args.nn_inputs):
        wanted_columns = args.nn_outputs + args.nn_inputs
        if(args.verbose):
            print("nn_inputs == {}\n".format(str(args.nn_inputs)))
        car_data_df = pd.read_csv(args.input_csv, nrows=5, usecols=wanted_columns)
    else:
        car_data_df = pd.read_csv(args.input_csv, nrows=5)

    # TODO clean up NANS and strings to be enums and values that can be used for training the neural network

    return car_data_df

def createTrainingData(args, car_df):
    Tvalues = car_df[args.nn_outputs].values
    Xvalues = car_df[args.nn_inputs].values
    if(args.verbose):
        print("Xvalues == {}\n".format(Xvalues[:10]))
        print("Tvalues == {}\n".format(Tvalues[:10]))

    return partition(Xvalues, Tvalues, shuffle=True)
    
def createCliNeuralNetwork(args, car_df, verbose=False):
    hidden_layers = [10, 10]
    if(args.hidden_units):
        hidden_layers = list(map(int, args.hidden_units.strip('[]').split(',')))
        if(verbose):
            print("hidden_layers == {}".format(str(hidden_layers)))
    
    outputCnt = len(args.nn_inputs)
    inputCnt = car_df.shape[1] - outputCnt
    nnet = NeuralNetworkTorch(inputCnt, hidden_layers, outputCnt)
    if(args.verbose):
        print(str(nnet))
    return nnet


if(__name__ == "__main__"):
    parser = createArgParser()
    args = parser.parse_args()
    if(args.nn_inputs):
        args.nn_inputs = list(map(str, args.nn_inputs.strip('[]').replace(" ", "").split(',')))

    if(args.nn_outputs):
        args.nn_outputs = list(map(str, args.nn_outputs.strip('[]').replace(" ", "").split(',')))

    usedCar_df = createPandasDataFrame(args)
    Xtrain, Ttrain, Xvalidate, Tvalidate, Xtest, Ttest = createTrainingData(args, usedCar_df)

    if(args.verbose):
        print("Xtrain == {}\nTtrain == {}\n".format(Xtrain, Ttrain))
        print("Xvalidate == {}\nTvalidate == {}\n".format(Xtrain, Ttrain))
        print("Xtest == {}\nTtest == {}\n".format(Xtrain, Ttrain))
        print("dataframe shape == {}\n".format(str(usedCar_df.shape)))

    nnet = createCliNeuralNetwork(args, usedCar_df, args.verbose)