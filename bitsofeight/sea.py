from OpenGL.GL import *
from wasabisg import shader
from wasabisg.scenegraph import ModelNode


sea_shader = shader.Shader(
    vert="""

varying vec3 normal;
varying vec3 pos; // position of the fragment in screen space
varying vec2 uv;

//uniform mat4 inv_view;

void main(void)
{
    vec4 a = gl_Vertex;
    gl_Position = gl_ModelViewProjectionMatrix * a;
    normal = (gl_NormalMatrix * gl_Normal).xyz;
    pos = (gl_ModelViewMatrix * a).xyz;
    uv = gl_MultiTexCoord0.st;
}
""",
    frag="""

varying vec3 normal;
varying vec3 pos;
varying vec2 uv;

uniform int num_lights;
uniform vec4 colours[8];
uniform vec4 positions[8];
uniform float intensities[8];
uniform float falloffs[8];
const vec3 diffuse_colour = vec3(0.2, 0.4, 0.6);
const vec4 specular = vec4(1.0, 1.0, 1.0, 1.0);
uniform vec4 ambient;
uniform vec3 camerapos;
const float specular_exponent = 30.0;

vec3 mod289(vec3 x)
{
  return x - floor(x * (1.0 / 289.0)) * 289.0;
}

vec4 mod289(vec4 x)
{
  return x - floor(x * (1.0 / 289.0)) * 289.0;
}

vec4 permute(vec4 x)
{
  return mod289(((x*34.0)+1.0)*x);
}

vec4 taylorInvSqrt(vec4 r)
{
  return 1.79284291400159 - 0.85373472095314 * r;
}

vec3 fade(vec3 t) {
  return t*t*t*(t*(t*6.0-15.0)+10.0);
}

// Classic Perlin noise
float cnoise(vec3 P)
{
  vec3 Pi0 = floor(P); // Integer part for indexing
  vec3 Pi1 = Pi0 + vec3(1.0); // Integer part + 1
  Pi0 = mod289(Pi0);
  Pi1 = mod289(Pi1);
  vec3 Pf0 = fract(P); // Fractional part for interpolation
  vec3 Pf1 = Pf0 - vec3(1.0); // Fractional part - 1.0
  vec4 ix = vec4(Pi0.x, Pi1.x, Pi0.x, Pi1.x);
  vec4 iy = vec4(Pi0.yy, Pi1.yy);
  vec4 iz0 = Pi0.zzzz;
  vec4 iz1 = Pi1.zzzz;

  vec4 ixy = permute(permute(ix) + iy);
  vec4 ixy0 = permute(ixy + iz0);
  vec4 ixy1 = permute(ixy + iz1);

  vec4 gx0 = ixy0 * (1.0 / 7.0);
  vec4 gy0 = fract(floor(gx0) * (1.0 / 7.0)) - 0.5;
  gx0 = fract(gx0);
  vec4 gz0 = vec4(0.5) - abs(gx0) - abs(gy0);
  vec4 sz0 = step(gz0, vec4(0.0));
  gx0 -= sz0 * (step(0.0, gx0) - 0.5);
  gy0 -= sz0 * (step(0.0, gy0) - 0.5);

  vec4 gx1 = ixy1 * (1.0 / 7.0);
  vec4 gy1 = fract(floor(gx1) * (1.0 / 7.0)) - 0.5;
  gx1 = fract(gx1);
  vec4 gz1 = vec4(0.5) - abs(gx1) - abs(gy1);
  vec4 sz1 = step(gz1, vec4(0.0));
  gx1 -= sz1 * (step(0.0, gx1) - 0.5);
  gy1 -= sz1 * (step(0.0, gy1) - 0.5);

  vec3 g000 = vec3(gx0.x,gy0.x,gz0.x);
  vec3 g100 = vec3(gx0.y,gy0.y,gz0.y);
  vec3 g010 = vec3(gx0.z,gy0.z,gz0.z);
  vec3 g110 = vec3(gx0.w,gy0.w,gz0.w);
  vec3 g001 = vec3(gx1.x,gy1.x,gz1.x);
  vec3 g101 = vec3(gx1.y,gy1.y,gz1.y);
  vec3 g011 = vec3(gx1.z,gy1.z,gz1.z);
  vec3 g111 = vec3(gx1.w,gy1.w,gz1.w);

  vec4 norm0 = taylorInvSqrt(vec4(dot(g000, g000), dot(g010, g010), dot(g100, g100), dot(g110, g110)));
  g000 *= norm0.x;
  g010 *= norm0.y;
  g100 *= norm0.z;
  g110 *= norm0.w;
  vec4 norm1 = taylorInvSqrt(vec4(dot(g001, g001), dot(g011, g011), dot(g101, g101), dot(g111, g111)));
  g001 *= norm1.x;
  g011 *= norm1.y;
  g101 *= norm1.z;
  g111 *= norm1.w;

  float n000 = dot(g000, Pf0);
  float n100 = dot(g100, vec3(Pf1.x, Pf0.yz));
  float n010 = dot(g010, vec3(Pf0.x, Pf1.y, Pf0.z));
  float n110 = dot(g110, vec3(Pf1.xy, Pf0.z));
  float n001 = dot(g001, vec3(Pf0.xy, Pf1.z));
  float n101 = dot(g101, vec3(Pf1.x, Pf0.y, Pf1.z));
  float n011 = dot(g011, vec3(Pf0.x, Pf1.yz));
  float n111 = dot(g111, Pf1);

  vec3 fade_xyz = fade(Pf0);
  vec4 n_z = mix(vec4(n000, n100, n010, n110), vec4(n001, n101, n011, n111), fade_xyz.z);
  vec2 n_yz = mix(n_z.xy, n_z.zw, fade_xyz.y);
  float n_xyz = mix(n_yz.x, n_yz.y, fade_xyz.x);
  return 2.2 * n_xyz;
}


vec3 calc_light(in vec3 frag_normal, in int lnum, in vec3 diffuse) {
    vec4 light = positions[lnum];
    float intensity = intensities[lnum];
    vec3 light_colour = colours[lnum].rgb;

    vec3 lightvec;

    if (light.w > 0.0) {
        lightvec = light.xyz - pos;

        // Use quadratic attenuation
        float lengthsq = dot(lightvec, lightvec);
        intensity /= 1.0 + lengthsq * falloffs[lnum];

        lightvec = normalize(lightvec);
    } else {
        lightvec = light.xyz;
    }

    float diffuse_component = dot(
        frag_normal, lightvec
    );
    diffuse_component = max(0.0, diffuse_component);

    float specular_component = 0.0;
    if (diffuse_component > 0.0) {
        vec3 rlight = reflect(lightvec, frag_normal);
        vec3 eye = normalize(pos);
        specular_component = pow(max(0.0, dot(eye, rlight)), specular_exponent);
    }

    return intensity * light_colour * (
        diffuse_component * diffuse +
        specular_component * specular.rgb
    );
}

uniform float t;

vec3 get_normal_offset(in vec3 wpos) {
    vec3 hashx = wpos + vec3(t * 0.3, 0.0, 0.0);
    vec3 hashy = wpos + vec3(0.0, 0.0, t * 0.77);
    vec3 hashz = wpos + vec3(0.0, t * 1.37, 0.0);

    return vec3(
        cnoise(hashx),
        cnoise(hashy),
        cnoise(hashz)
    );
}

const vec3 sky_colour = vec3(0.4, 0.4, 0.8);

void main (void) {
    int i;

    vec3 wpos = vec3(uv.x * 1000.0, 0.0, uv.y * 1000.0) - camerapos;

    float dist = length(pos);

    vec3 n = normalize(normal + (0.2 / pow(1.0 + dist / 80.0, 3.0)) * get_normal_offset(wpos));
    vec3 colour = vec3(0, 0, 0);
    vec3 basecolour = diffuse_colour;

    colour += basecolour * ambient.rgb;

    for (i = 0; i < num_lights; i++) {
        colour += calc_light(n, i, basecolour);
    }
    gl_FragColor = vec4(colour.xyz, 1.0);
}
""",
    name='sea_shader'
)


class SeaNode(ModelNode):
    t = 0
    def update(self, dt):
        self.t += dt

    def draw_inner(self, camera):
        self.t += 0.02
        if shader.activeshader == self.shader:
            self.shader.uniformf('t', self.t)
            self.shader.uniformf('camerapos', *self.pos)
        super(SeaNode, self).draw_inner(camera)
