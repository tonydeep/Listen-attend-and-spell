'''@file decoder.py
neural network decoder environment'''

import tensorflow as tf
import numpy as np
from neuralnetworks.classifiers import seq_convertors
from IPython.core.debugger import Tracer; debug_here = Tracer();

class Decoder(object):
    '''Class for the decoding environment for a neural net classifier'''

    def __init__(self, classifier, input_dim, max_length):
        '''
        NnetDecoder constructor, creates the decoding graph

        Args:
            classifier: the classifier that will be used for decoding
            input_dim: the input dimension to the nnnetgraph
        '''

        self.graph = tf.Graph()
        self.max_length = max_length

        with self.graph.as_default():

            #create the inputs placeholder
            self.inputs = tf.placeholder(
                tf.float32, shape=[max_length, input_dim], name='inputs')

            #create the sequence length placeholder
            self.seq_length = tf.placeholder(
                tf.int32, shape=[1], name='seq_length')

            split_inputs = tf.unpack(tf.expand_dims(self.inputs, 1))

            #create the decoding graph
            logits, _, self.saver, _ = classifier(split_inputs,
                                                  self.seq_length,
                                                  is_training=False,
                                                  reuse=False,
                                                  scope='Classifier')

            #convert logits to non sequence for the softmax computation
            logits = seq_convertors.seq2nonseq(logits, self.seq_length)

            #compute the outputs
            self.outputs = tf.nn.softmax(logits)

        #specify that the graph can no longer be modified after this point
        self.graph.finalize()

    def __call__(self, inputs):
        '''decode using the neural net

        Args:
            inputs: the inputs to the graph as a NxF numpy array where N is the
                number of frames and F is the input feature dimension

        Returns:
            an NxO numpy array where N is the number of frames and O is the
                neural net output dimension
        '''

        #get the sequence length
        seq_length = [inputs.shape[0]]

        #pad the inputs
        inputs = np.append(
            inputs, np.zeros([self.max_length-inputs.shape[0], inputs.shape[1]])
            , 0)

        #pylint: disable=E1101
        return self.outputs.eval(feed_dict={self.inputs:inputs,
                                            self.seq_length:seq_length})

    def restore(self, filename):
        '''
        load the saved neural net

        Args:
            filename: location where the neural net is saved
        '''

        self.saver.restore(tf.get_default_session(), filename)

class LasDecoder(Decoder):
    def __init__(self, classifier, input_dim, max_length, batch_size):
        '''
        Las Decoder constructor, creates the decoding graph
        The decoder expects a batch size of one utterance for now.

        Args:
            classifier: the classifier that will be used for decoding.
            input_dim: the input dimension to the classifier.
        '''

        self.graph = tf.Graph()
        self.max_length = max_length
        self.input_dim = input_dim
        self.batch_size = batch_size

        with self.graph.as_default():

            #create the inputs placeholder
            self.inputs = tf.placeholder(
                tf.float32, shape=[self.batch_size, max_length, input_dim],
                name='inputs')

            #create the sequence length placeholder
            self.seq_length = tf.placeholder(
                tf.int32, shape=[self.batch_size], name='seq_length')

            #create the decoding graph
            logits, _, self.saver, _ = classifier(self.inputs,
                                                  self.seq_length,
                                                  is_training=False,
                                                  reuse=False,
                                                  scope='Classifier',
                                                  targets=None,
                                                  target_seq_length=None)

            #compute the outputs
            self.outputs = tf.nn.softmax(logits)

        #specify that the graph can no longer be modified after this point
        self.graph.finalize()

    def __call__(self, inputs):
        '''decode using the neural net

        Args:
            inputs: the inputs to the graph as a NxF numpy array where N is the
                number of frames and F is the input feature dimension

        Returns:
            an NxO numpy array where N is the number of frames and O is the
                neural net output dimension
        '''

        #get the sequence length
        input_seq_length = [i.shape[0] for i in inputs]

        #pad the inputs with zeros. Their shape will be the same after this.
        inputs = [np.pad(i,
                         ((0, self.max_length-i.shape[0]), (0, 0)),
                         'constant') for i in inputs]

        #pylint: disable=E1101
        return self.outputs.eval(feed_dict={self.inputs:inputs,
                                            self.seq_length:input_seq_length})