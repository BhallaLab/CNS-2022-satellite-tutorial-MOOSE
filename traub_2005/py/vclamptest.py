# vclamptest.py --- 
# 
# Filename: vclamptest.py
# Description: 
# Author: 
# Maintainer: 
# Created: Wed Feb  6 16:25:52 2013 (+0530)
# Version: 
# Last-Updated: Sun Jun 25 14:47:22 2017 (-0400)
#           By: subha
#     Update #: 149
# URL: 
# Keywords: 
# Compatibility: 
# 
# 

# Commentary: 
# 
# Set up a voltage clamp experiment with specified series of clamping
# voltage values
# 
# 

# Change log:
# 
# 
# 
# 
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 3, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program; see the file COPYING.  If not, write to
# the Free Software Foundation, Inc., 51 Franklin Street, Fifth
# Floor, Boston, MA 02110-1301, USA.
# 
# 

# Code:

import numpy as np
import sys
sys.path.append('../../../python')
import moose
from moose import utils
# import cells

def vclamptest(axon, vclamp, duration=50e-3, delay=150e-3, solver='ee', vhold=None, mc=None, dc=None, simdt=1e-5, plotdt=0.25e-3):
    """Do a series of voltage clamp experiemnts on axon.

    parameters:
    
    axon: Compartment object to be voltage clamped

    vclamp: array of clamping voltage values.

    duration: duration of each clamp

    delay: delay between successive application of clamping voltages

    vhold: holding voltage, If None, the Em of the
    axon is used.

    mc: model container, the vclamp object will be created inside
    mc/electronics. If None, we use axon.parent.parent

    dc: data container, the data recording tables will be created
    inside it. If None, we use axon.parent.parent
    """
    if vhold is None:
        vhold = axon.C.Em
    if mc is None:
        mc = axon.C.parent.parent
    if dc is None:
        dc = axon.C.parent.parent
    electronics = moose.Neutral('%s/electronics' % (mc.path))
    command = moose.PulseGen('%s/command_source' % (electronics.path))
    clamp = moose.VClamp('%s/vclamp' % (electronics.path))
    moose.connect(command, 'output', clamp, 'commandIn')
    moose.connect(axon.C, 'VmOut', clamp, 'sensedIn')
    moose.connect(clamp, 'currentOut', axon.C, 'injectMsg')
    simtime = 0
    command.count = len(vclamp)
    command.baseLevel = vhold
    for ii, clamping_voltage in enumerate(vclamp):
        simtime += delay + duration
        command.delay[ii] = delay
        command.width[ii] = duration
        command.level[ii] = clamping_voltage
    injected = moose.Table('%s/Iinject' % (dc.path))
    moose.connect(injected, 'requestOut', clamp, 'getCurrent')
    voltage = moose.Table('%s/Vcommand' % (dc.path))
    moose.connect(voltage, 'requestOut', command, 'getOutputValue')
    vm = moose.Table('%s/Vm' % (dc.path))
    moose.connect(vm, 'requestOut', axon.C, 'getVm')
    utils.resetSim([mc.path, dc.path], simdt, plotdt, simmethod=solver)
    moose.start(simtime)
    ivec = np.asarray(injected.vector)
    vvec = np.asarray(voltage.vector)
    vmvec = np.asarray(vm.vector)
    ts = np.linspace(0, simtime, len(vvec))
    sidx = np.nonzero(np.diff(vvec) > 0)[0]
    eidx = np.nonzero(np.diff(vvec) < 0)[0]
    iarrays = []
    for ii in range(len(vclamp)):
        iarrays.append(ivec[sidx[ii]: eidx[ii]].copy())
    return {
        "Vm": vmvec,
        "commandVoltage": vvec,
        "inject": ivec,
        "ts": ts,
        "injectArrays": iarrays}


from matplotlib import pyplot as plt
sys.path.append('../../squid')
from squid import SquidAxon


def test():
    mc = moose.Neutral('model')
    dc = moose.Neutral('data')
    nrn = moose.Neuron('%s/nrn' % (mc.path))
    x = SquidAxon('%s/squid' % (nrn.path))
    clampv = [10.0, 20.0, 30.0, 40.0, 50.0]
    data = vclamptest(x, clampv, duration=20.0, delay=100.0, vhold=0.0, mc=mc, dc=dc, simdt=1e-2, plotdt=1e-2, solver='hsolve')
    plt.subplot(311)
    plt.title('Membrane potential throughout experiment')
    plt.plot(data['ts'], data['Vm'], label='Vm')
    plt.legend()
    plt.subplot(312)
    plt.title('Injection current throughout experiment')
    plt.plot(data['ts'], data['inject'], label='Inject')
    plt.legend()
    plt.subplot(313)
    plt.title('Injection currents for different clamp volatge values')
    for ii, inject in enumerate(data['injectArrays']):
        plt.plot(inject, label='V = %g' % (clampv[ii]))
    plt.legend()
    plt.show()

if __name__ == '__main__':
    test()
    
    


# 
# vclamptest.py ends here