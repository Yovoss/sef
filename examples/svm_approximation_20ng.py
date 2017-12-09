# License: MIT License https://github.com/passalis/sef/blob/master/LICENSE.txt
from __future__ import absolute_import, division, print_function, unicode_literals

import numpy as np
import sklearn
from sklearn import svm, grid_search
from sklearn.preprocessing import MinMaxScaler

from classification import evaluate_svm, evaluate_ncc
from newsgroups import load_20ng_dataset_bow
from sef_dr.linear import LinearSEF
from sklearn.preprocessing import StandardScaler

def unsupervised_approximation(method='pca'):
    # Load the data and init seeds
    train_data, train_labels, test_data, test_labels = load_20ng_dataset_bow()
    np.random.seed(1)
    sklearn.utils.check_random_state(1)
    n_train = 5000

    if method == 'svm':
        acc = evaluate_svm(train_data[:n_train, :], train_labels[:n_train], test_data, test_labels)
    elif method == 'ncc':
        acc = evaluate_ncc(train_data[:n_train, :], train_labels[:n_train], test_data, test_labels)

    elif method == 'S-SVM-A-10d' or method == 'S-SVM-A-20d':

        # Learn an SVM

        parameters = {'kernel': ['linear'], 'C': [0.0001, 0.001, 0.01, 0.1, 1, 10, 100, 1000, 10000, 100000]}
        model = grid_search.GridSearchCV(svm.SVC(max_iter=10000, decision_function_shape='ovo'), parameters, n_jobs=-1,
                                         cv=3)
        model.fit(train_data[:n_train], train_labels[:n_train])

        params = {'model': model, 'n_labels': np.unique(train_labels).shape[0], 'scaler': None}

        # Learn a similarity embedding
        if method == 'S-SVM-A-10d':
            dims = 10
        else:
            dims = 20
        proj = LinearSEF(train_data.shape[1], output_dimensionality=dims)
        proj.cuda()
        loss = proj.fit(data=train_data[:n_train, :], target_data=train_data[:n_train, :],
                        target_labels=train_labels[:n_train], target='svm', target_params=params, epochs=50,
                        learning_rate=0.001, batch_size=128, verbose=True, regularizer_weight=0.001)

        acc = evaluate_ncc(proj.transform(train_data[:n_train, :]), train_labels[:n_train],
                           proj.transform(test_data), test_labels)

    print("Method: ", method, " Test accuracy: ", 100 * acc, " %")

if __name__ == '__main__':
    print("Evaluating baseline SVM ...")
    unsupervised_approximation('svm')

    print("Evaluating baseline NCC")
    unsupervised_approximation('ncc')

    print("Evaluating SVM-based analysis 10d")
    unsupervised_approximation('S-SVM-A-10d')

    print("Evaluating SVM-based analysis 20d")
    unsupervised_approximation('S-SVM-A-20d')
