__author__ = "Peter Bennett"
__copyright__ = "Copyright 2013, Peter A Bennett"
__license__ = "LGPL"
__maintainer__ = "Peter Bennett"
__email__ = "pab850@gmail.com"
__contact__ = "www.bytebash.com"

from utilities import *
from math import *
import numpy as np
from vector import Vector2, Vector3
from ctypes import pointer, sizeof

class Tessendorf():
    def __init__(self, dimension=64, A=0.0005, w=Vector2(32.0, 32.0), length=64, period=200.0):
        self.N = dimension              # Dimension - should be power of 2
        self.N1 = self.N+1              # Vertex grid has additional row and
                                        # column for tiling purposes
        self.NSq = self.N * self.N
        self.N1Sq = self.N1 * self.N1
        self.NVec = self.N1Sq * 3       # Number of floats for vector data
        self.length = float(length)     # Length Parameter
        self.w = w                      # Wind Parameter
        self.a = A                      # Phillips spectrum parameter, affects heights of waves
        self.w0 = 2.0 * pi / period     # Used by the dispersion function
        self.g = 9.81                   # Constant acceleration due to gravity
                       
        # Wave surface property arrays (displacements, normals, etc)
        self.hTilde0 = np2DArray(0.0+0j,self.N,self.N)      # Height @ t = 0
        self.hTilde0mk = np2DArray(0.0+0j,self.N,self.N)    # H conjugate @t = 0
        self.hTilde = np2DArray(0.0+0j,self.N,self.N)       # Height @ t
        self.hTildeSlopeX = np2DArray(0.0+0j,self.N,self.N) # NormalX @ t
        self.hTildeSlopeZ = np2DArray(0.0+0j,self.N,self.N) # NormalZ @ t
        self.hTildeDx = np2DArray(0.0+0j,self.N,self.N)     # DisplacementX @ t
        self.hTildeDz = np2DArray(0.0+0j,self.N,self.N)     # DisplacementZ @ t
        
        # Lookup tables for code optimisation
        self.dispersionLUT = np2DArray(0.0, self.N, self.N) # Dispersion Lookup
        self.kxLUT = np2DArray(0.0, self.N, self.N)         # kx Lookup
        self.kzLUT = np2DArray(0.0, self.N, self.N)         # kz Lookup
        self.lenLUT = np2DArray(0.0, self.N, self.N)        # Length Lookup
                                        
        # Build Lookup Tables and vertex indices list (N*N)        
        for i in range(self.N):
            # Build k LUT for wave evaluation loop
            kz = pi * (2.0 * i - self.N) / self.length
            for j in range(self.N):
                kx = pi * (2.0 * j - self.N) / self.length
                # Generate index LUT
                self.kxLUT[i][j] = kx
                self.kzLUT[i][j] = kz
                # Generate HTilde initial values
                self.hTilde0[i][j] = self.getHTilde0(j, i)
                self.hTilde0mk[i][j] = self.getHTilde0(-j, -i).conjugate()      
                # Build a dispersion LUT
                self.dispersionLUT[i][j] = self.dispersion(j, i) 
                # Build a length LUT
                self.lenLUT[i][j] = sqrt(kx * kx + kz * kz)
        
    def phillips(self, nPrime, mPrime):
        ''' The phillips spectrum '''
        k = Vector2(pi * (2 * nPrime - self.N) / self.length, \
                    pi * (2 * mPrime - self.N) / self.length)

        k_length = k.magnitude()
        
        if(k_length < 0.000001): return 0.0
        
        k_length2 = k_length * k_length
        k_length4 = k_length2 * k_length2
        
        k_dot_w = k.normalise().dot(self.w.normalise())
        k_dot_w2 = k_dot_w * k_dot_w * k_dot_w * k_dot_w * k_dot_w * k_dot_w
        
        w_length = self.w.magnitude()
        L = w_length * w_length / self.g
        l2 = L*L

        damping = 0.001
        ld2 = l2 * damping * damping
        
        return self.a * exp(-1.0 / (k_length2 * l2)) / k_length4 * k_dot_w2 * \
               exp(-k_length2 * ld2);

    def dispersion(self, nPrime, mPrime):
        kx = pi * (2.0 * nPrime - self.N) / self.length
        kz = pi * (2.0 * mPrime - self.N) / self.length
        return floor(sqrt(self.g * sqrt(kx**2 + kz**2)) / self.w0) * self.w0
           
    def getHTilde0(self, nPrime, mPrime):
        r = gaussianRandomVariable()
        return r * sqrt(self.phillips(nPrime, mPrime) / 2.0)
        
    def genHTildeArray(self, t):
        ''' Generate array of wave height values for time t '''
        omegat = self.dispersionLUT * t
        
        sin_ = np.sin(omegat)
        cos_ = np.cos(omegat)
        
        c0 = cos_ + (sin_ * 1j)
        c1 = cos_ + (-sin_ * 1j)
    
        self.hTilde = self.hTilde0 * c0 + self.hTilde0mk * c1 

    def genHTilde(self, t):
        ''' Generate hTilde for time t '''
        # Update the hTilde values
        self.genHTildeArray(t)
        # Generate normals for X and Z
        self.hTildeSlopeX = self.hTilde * self.kxLUT * 1j
        self.hTildeSlopeZ = self.hTilde * self.kzLUT * 1j
        # Generate a set of indices for which the length in the length 
        # look-up table is less than 0.000001
        zeros = self.lenLUT < 0.000001
        nonzeros = self.lenLUT >= 0.000001
        # If the length contained in the length look-up table (lenLUT) is 
        # greater than 0.000001 set the displacements in x and z to:
        # Dx = hTilde * complex(0.0,-kx/length)
        # Dz = hTilde * complex(0.0,-kz/length)
        # Otherwise, set the displacements to 0.0+0j
        self.hTildeDx = self.hTilde * 1j * -self.kxLUT / self.lenLUT
        self.hTildeDz = self.hTilde * 1j * -self.kzLUT / self.lenLUT
        self.hTildeDx[zeros] = 0.0+0j
        self.hTildeDz[zeros] = 0.0+0j

    def doFFT(self):
        ''' Compute FFT '''
        # Heights
        self.hTilde = np.fft.fft2(self.hTilde)
        # Displacements
        self.hTildeDx = np.fft.fft2(self.hTildeDx)
        self.hTildeDz = np.fft.fft2(self.hTildeDz)
        # Normals
        self.hTildeSlopeX = np.fft.fft2(self.hTildeSlopeX)
        self.hTildeSlopeZ = np.fft.fft2(self.hTildeSlopeZ)
         
    def evaluateWavesFFT(self, t):
        self.genHTilde(t)
        self.doFFT()
         
    def update(self, time, verts, v0):
        '''
        Update the input vertex arrays
        # Vertex arrays are 3-dimensional have have the following structure:
        [
         [[v0x,v0y,v0z,n0x,n0y,n0z],[v1x,v1y,v1z,n1x,n1y,n1z]],
         [[v2x,v2y,v2z,n2x,n2y,n2z],[v3x,v3y,v3z,n3x,n3y,n3z]],
         [[v4x,v4y,v4z,n4x,n4y,n4z],[v5x,v5y,v5z,n5x,n5y,n5z]]
        ]
        Positions and normals are sampled from the heightfield and applied to
        the input array.
        verts: input array to be modified
        v0: the original vertex positions
        '''
        
        # First, do a surface update
        self.evaluateWavesFFT(time)

        # Apply -1**x, -1**z factors
        self.hTildeSlopeX[::2,::2] = -self.hTildeSlopeX[::2,::2]
        self.hTildeSlopeX[1::2,1::2] = -self.hTildeSlopeX[1::2,1::2]
        self.hTildeSlopeZ[::2,::2] = -self.hTildeSlopeZ[::2,::2]
        self.hTildeSlopeZ[1::2,1::2] = -self.hTildeSlopeZ[1::2,1::2]
        self.hTilde = -self.hTilde
        self.hTilde[::2,::2] = -self.hTilde[::2,::2]
        self.hTilde[1::2,1::2] = -self.hTilde[1::2,1::2]
        self.hTildeDx[::2,::2] = -self.hTildeDx[::2,::2]
        self.hTildeDx[1::2,1::2] = -self.hTildeDx[1::2,1::2]
        self.hTildeDz[::2,::2] = -self.hTildeDz[::2,::2]
        self.hTildeDz[1::2,1::2] = -self.hTildeDz[1::2,1::2]
                           
        # Update the vertex list for all elements apart from max indices
        # Position X,Y,Z
        verts[:self.N:,:self.N:,0] = v0[:self.N:,:self.N:,0] + self.hTildeDx * -1
        verts[:self.N:,:self.N:,1] = self.hTilde
        verts[:self.N:,:self.N:,2] = v0[:self.N:,:self.N:,2]  + self.hTildeDz * -1
        # Normal X,Y,Z
        verts[:self.N:,:self.N:,3] = -self.hTildeSlopeX
        verts[:self.N:,:self.N:,4] = 1.0
        verts[:self.N:,:self.N:,5] = -self.hTildeSlopeZ
        
        # Allow seamless tiling:

        # Top index of vertices - reference bottom index of displacement array
        # vertices(N,N) = original(N,N) + hTilde(0,0) * - 1
        # Position X,Y,Z
        verts[self.N,self.N,0] = v0[self.N,self.N,0] + \
                                      self.hTildeDx[0,0] * -1                         
        verts[self.N,self.N,1] = self.hTilde[0,0]
        verts[self.N,self.N,2] = v0[self.N,self.N,2] + \
                                      self.hTildeDz[0,0] * -1
        # Normal X,Y,Z                    
        verts[self.N,self.N,3] = -self.hTildeSlopeX[0,0]
        verts[self.N,self.N,4] = 1.0
        verts[self.N,self.N,5] = -self.hTildeSlopeZ[0,0]
        
        # Last row of vertices - Reference first row of the displacement array
        # vertices(N,[0..N]) = original(N,[0..N]) + hTilde(0,[0..N]) * -1
        # Position X,Y,Z
        verts[self.N,0:self.N:,0] = v0[self.N,0:self.N:,0] + \
                                         self.hTildeDx[0,0:self.N:] * -1                        
        verts[self.N,0:self.N:,1] = self.hTilde[0,0:self.N:]
        verts[self.N,0:self.N:,2] = v0[self.N,0:self.N:,2] + \
                                         self.hTildeDz[0,0:self.N:] * -1
        # Normal X,Y,Z                          
        verts[self.N,0:self.N:,3] = -self.hTildeSlopeX[0,0:self.N:]
        verts[self.N,0:self.N:,4] = 1.0
        verts[self.N,0:self.N:,5] = -self.hTildeSlopeZ[0,0:self.N:]
        
        # Last col of vertices - Reference first col of the displacement array
        # vertices([0..N],N) = original([0..N],N) + hTilde([0..N],0) * -1
        # Position X,Y,Z
        verts[0:self.N:,self.N,0] = v0[0:self.N:,self.N,0] + \
                                         self.hTildeDx[0:self.N:,0] * -1 
        verts[0:self.N:,self.N,1] = self.hTilde[0:self.N:,0]
        verts[0:self.N:,self.N,2] = v0[0:self.N:,self.N,2] + \
                                         self.hTildeDz[0:self.N:,0] * -1
        # Normal X,Y,Z                          
        verts[0:self.N:,self.N,3] = -self.hTildeSlopeX[0:self.N:,0]
        verts[0:self.N:,self.N,4] = 1.0
        verts[0:self.N:,self.N,5] = -self.hTildeSlopeZ[0:self.N:,0]


    