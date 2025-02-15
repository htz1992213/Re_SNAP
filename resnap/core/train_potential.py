# coding: utf-8
# Copyright (c) Tingzheng Hou and Lu Jiang.
# Distributed under the terms of the MIT License.

"""
This module implements a core class PotentialTrainer for training/making
potential of Re using a training dataset containing number of atoms,
structural bispectrum terms and energy.

"""

import numpy as np
import matplotlib.pyplot as plt
import sklearn.linear_model
from sklearn.preprocessing import normalize
from scipy import io
import os

__author__ = "Tingzheng Hou and Lu Jiang"
__copyright__ = "Copyright 2020, Tingzheng Hou and Lu Jiang"
__version__ = "1.0"
__maintainer__ = "Lu Jiang"
__email__ = "lu_jiang@berkeley.edu"
__date__ = "May 3, 2020"

MODELS = {"LASSO": sklearn.linear_model.Lasso,
          "RIDGE": sklearn.linear_model.Ridge}


class PotentialTrainer:

    def __init__(self, data_dir, f, norm=None):
        """
        Base constructor.

        Args:
            data_dir (str): directory to the training data files.
            f (func): training model function.
            norm (str): The norm to use to normalize features. If
                None, apply no normalization.

        """
        self.data_dir = data_dir
        self.f = MODELS.get(f)
        data = io.loadmat(self.data_dir)
        for data_name in ["X", "y"]:
            print("\nloaded %s data!" % data_name)
            print(data[data_name].shape)
        self.training_x = data.get('X')
        self.norm = norm
        if self.norm:
            features = self.training_x[:, 1:]
            features, norms = normalize(features, norm=self.norm,
                                        axis=0, copy=True, return_norm=True)
            self.norms = norms
            self.training_x[:, 1:] = features
        self.training_y = data.get('y')
        self.training_data = \
            np.concatenate((self.training_y, self.training_x), axis=1)

    @staticmethod
    def plot_y_yhat_atom(y, y_hat):
        """
        y vs y_hat plotter.

        Args:
            y (list or numpy.array): true labels.
            y_hat (list or numpy.array): predicted labels.

        """
        plt.figure(figsize=(8, 8))
        linear_regressor = sklearn.linear_model.LinearRegression()
        linear_regressor.fit(y.reshape(-1, 1), y_hat)
        y_pred = linear_regressor.predict(y.reshape(-1, 1))
        plt.plot(y, y_pred, c="red", linewidth=3, alpha=0.3)
        plt.scatter(y, y_hat, s=20, c="deepskyblue", alpha=0.1)
        plt.xticks(size=15)
        plt.yticks(size=15)
        plt.ylabel('$\hat{y}$ (eV/atom)', size=15)
        plt.xlabel('y (eV/atom)', size=15)
        plt.show()

    @staticmethod
    def plot_y_yhat(y, y_hat, num_array):
        """
        y vs y_hat plotter.

        Args:
            y (list or numpy.array): true labels.
            y_hat (list or numpy.array): predicted labels.
            num_array (list or numpy.array): number of atoms
                in each sample.

        """
        y = y * num_array
        y_hat = y_hat * num_array
        plt.figure(figsize=(8, 8))
        linear_regressor = sklearn.linear_model.LinearRegression()
        linear_regressor.fit(y.reshape(-1, 1), y_hat)
        y_pred = linear_regressor.predict(y.reshape(-1, 1))
        plt.plot(y, y_pred, c="red", linewidth=3, alpha=0.3)
        plt.scatter(y, y_hat, s=20, c="deepskyblue", alpha=0.1)
        plt.xticks(size=15)
        plt.yticks(size=15)
        plt.ylabel('$\hat{y}$ (eV)', size=15)
        plt.xlabel('y (eV)', size=15)
        plt.show()

    @staticmethod
    def plot_y_yhat_heat(y, y_hat):
        """
        y vs y_hat plotter.

        Args:
            y (list or numpy.array): true labels.
            y_hat (list or numpy.array): predicted labels.

        """
        plt.figure(figsize=(8, 8))
        linear_regressor = sklearn.linear_model.LinearRegression()
        linear_regressor.fit(y.reshape(-1, 1), y_hat)
        plt.figure(figsize=(13, 10))
        plt.hist2d(y, y_hat, (300, 300), cmap='jet')
        plt.colorbar()
        plt.xticks(size=15)
        plt.yticks(size=15)
        plt.ylabel('$\hat{y}$ (eV/atom)', size=15)
        plt.xlabel('y (eV/atom)', size=15)
        plt.show()

    def cross_validation(self, alpha_range, max_iter=1e6, tol=1e-4,
                         plot_image=None, seed=2020):
        """
         Cross validation test over a range of alpha.

         Args:
             alpha_range (list or numpy.array): a list of alpha values.
             max_iter (int): The maximum number of iterations.
             tol (int): The tolerance for the optimization.
             plot_image (str): The type of image to plot.
             seed (int): numpy random seed for shuffling data.

         """
        data = self.training_data.copy()
        np.random.seed(seed)
        np.random.shuffle(data)
        training_x = data[:, 1:]
        training_y = data[:, 0]
        num_array = data[:, 1]
        alpha_errors = []
        for alpha in alpha_range:
            print(r"5-fold error with alpha = {}".format(alpha))
            errors_validation = []
            errors_train = []
            for i in range(5):
                all_id = list(range(len(data)))
                validation_id = all_id[i::5]
                train_id = [i for i in all_id if i not in validation_id]
                train_x, train_y = training_x[train_id], training_y[train_id]
                validation_x,  validation_y = \
                    training_x[validation_id],  training_y[validation_id]
                num_array_train, num_array_val = \
                    num_array[train_id], num_array[validation_id]
                model = self.f(alpha=alpha, max_iter=max_iter, tol=tol,
                               fit_intercept=False)
                model.fit(train_x, train_y)
                predicted_validation = model.predict(validation_x)
                predicted_train = model.predict(train_x)
                diff_val = np.absolute(validation_y - predicted_validation)
                error_val = np.average(diff_val / num_array_val)
                diff_train = np.absolute(train_y - predicted_train)
                error_train = np.average(diff_train / num_array_train)
                if i == 0 and plot_image == "atom":
                    self.plot_y_yhat_atom(train_y / num_array_train,
                                          predicted_train / num_array_train)
                    self.plot_y_yhat_atom(validation_y / num_array_val,
                                          predicted_validation / num_array_val)
                if i == 0 and plot_image == "sample":
                    self.plot_y_yhat(train_y / num_array_train,
                                     predicted_train / num_array_train,
                                     num_array_train)
                    self.plot_y_yhat(validation_y / num_array_val,
                                     predicted_validation / num_array_val,
                                     num_array_val)
                errors_validation.append(error_val)
                errors_train.append(error_train)
            mean_train_e = np.mean(errors_train)
            mean_val_e = np.mean(errors_validation)
            print("Mean error train: {} eV/atom".format(mean_train_e))
            print("Mean error validaiton: {} eV/atom".format(mean_val_e))
            alpha_errors.append(np.mean(errors_validation))
        alpha_errors = np.array(alpha_errors)
        max_e = max(alpha_errors)
        min_e = min(alpha_errors)
        diff = max_e - min_e
        print(alpha_errors)
        self.plot_cross(alpha_range, alpha_errors, min_e - diff, max_e + diff)
        return alpha_errors

    @staticmethod
    def plot_cross(param, error, y_low, y_up):
        """
         Hyperparameter vs error plotter.

         Args:
             param (numpy.array or list): a list of alpha values.
             error (numpy.array or list): The maximum number of iterations.
             y_low (float): y axis lower limit.
             y_up (float): y axis upper limit.

         """
        x = np.arange(len(error))
        plt.plot(x, error, linewidth=2, color='red', marker='.', markersize=12)
        plt.xticks(x, param)
        plt.ylim(y_low, y_up)
        plt.ylabel('Mean validation error (eV/atom)')
        plt.xlabel('Hyperparameter')
        plt.show()

    def make_potential(self, output_dir, alpha=1.0, max_iter=1e6, tol=1e-4):
        """
         Generate and save Re potential.

         Args:
             output_dir (str): directory to save the potential file.
             alpha (float): Constant that multiplies the penalization term.
             max_iter (int): The maximum number of iterations.
             tol (int): The tolerance for the optimization.

         """
        model = self.f(alpha=alpha, max_iter=max_iter, tol=tol,
                       fit_intercept=False)
        model.fit(self.training_x, self.training_y)
        potential = model.coef_[0]
        print("Fitted potential: ", potential)
        if self.norm:
            potential = potential / self.norms
            print("Fitted unnormalized potential: ", potential)
        with open(os.path.join(output_dir, "re_potential"), 'w') as f:
            for i in range(len(potential)):
                f.write(str(potential[i]) + "\n")
            f.close()
