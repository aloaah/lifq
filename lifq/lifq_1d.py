import brian2 as b2
import numpy as np


class Lifq_1d:
    def __init__(self):
        self.state = None
        self.spike = None
        self.matrix = None
        self.reconstr_array = None

    def simulate_LIF_neuron(self, input_current, N, simulation_time, v_rest,
                            v_reset, firing_threshold, membrane_resistance, membrane_time_scale,
                            abs_refractory_period):
        # differential equation of Leaky Integrate-and-Fire model
        eqs = """
        dv/dt =
        ( -(v-v_rest) + membrane_resistance * input_current(t, i) ) / membrane_time_scale : volt (unless refractory)"""

        # LIF neuron using Brian2 library
        neuron = b2.NeuronGroup(
            N, model=eqs, reset="v=v_reset", threshold="v>firing_threshold",
            refractory=abs_refractory_period, method="euler")
        neuron.v = v_rest  # set initial value

        # monitoring membrane potential of neuron and injecting current
        state_monitor = b2.StateMonitor(neuron, ["v"], record=True)
        spike_monitor = b2.SpikeMonitor(neuron)
        # run the simulation
        b2.run(simulation_time)
        return state_monitor, spike_monitor

    # Rewrite the input signal  into the type for brian2 neuron models

    def create_time_matrix1D(self, matrix, time, simulation_time):
        big_matrix = np.empty(np.int64(np.ceil(simulation_time / time)), )
        for i in range(len(matrix)):
            temp = np.hstack(
                c for c in np.full(
                    (np.int64(
                        np.ceil(
                            simulation_time /
                            time)),
                        1),
                    matrix[i]))
            big_matrix = np.vstack((big_matrix, temp))
        big_matrix = np.delete(big_matrix, 0, 0)
        return b2.TimedArray(np.transpose(big_matrix) * b2.mA, dt=time)

       # Reconstruction of the input from the output of the model
    def decode(self, spike_count, firing_threshold,
               membrane_time_scale, membrane_resistance, simulation_time, n):
        dict_u_hat = dict()
        for values in np.unique(spike_count):
            if values == 0:
                dict_u_hat[values] = 0
            else:
                d_u_hat = simulation_time / values
                dict_u_hat[values] = (
                    ((firing_threshold / (1 - np.exp(-(d_u_hat / membrane_time_scale)))) * (1 / membrane_resistance)) / b2.mA)
        temp = np.ndarray((n, 1))
        for i in range(len(spike_count)):
            temp[i] = dict_u_hat[spike_count[i]]
        return temp

    def fit(self, X, simulation_time=66 * b2.ms, v_rest=0 * b2.mV,
            v_reset=0 * b2.mV, firing_threshold=0.09 * b2.mV,
            membrane_time_scale=7 * b2.ms, membrane_resistance=550 * b2.mohm, abs_refractory_period=0 * b2.ms, logger=False):
        assert X.ndim == 1, "Dimmention Error"

        if logger:
            b2.BrianLogger.log_level_debug()

        self.matrix = self.create_time_matrix1D(
            X, simulation_time, simulation_time)
        self.state, self.spike = self.simulate_LIF_neuron(self.matrix, len(X), simulation_time, v_rest,
                                                          v_reset, firing_threshold, membrane_resistance,
                                                          membrane_time_scale, abs_refractory_period)
        self.reconstr_array = self.decode(
            self.spike.count,
            firing_threshold,
            membrane_time_scale,
            membrane_resistance,
            simulation_time,
            len(X))

    def getSpike(self):
        if not isinstance(self.spike, type(None)):
            return self.spike
        else:
            raise AttributeError("You cannot call getSpike before fit")

    def getState(self):
        if not isinstance(self.state, type(None)):
            return self.state
        else:
            raise AttributeError("You cannot call getState before fit")

    def getDecodedSignal(self):
        if not isinstance(self.reconstr_array, type(None)):
            return self.reconstr_array
        else:
            raise AttributeError("You cannot call getDecodedSignal before fit")
