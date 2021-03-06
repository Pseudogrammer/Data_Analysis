# the darkspace dataset http://data.caida.org/datasets/security/telescope-educational/

import matplotlib

matplotlib.use('Agg')
from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import numpy as np
from scipy.stats import kendalltau
from sklearn import linear_model

pdf = PdfPages("internet.pdf")

df = pd.read_csv("traffic_stats.csv")

for i in range(4):
    plt.clf()
    plt.axes([0.17, 0.1, 0.75, 0.8])
    plt.plot(df.iloc[:, i])
    plt.grid(True)
    plt.xlabel("Minutes", size=15)
    plt.ylabel(df.columns[i], size=15)
    pdf.savefig()

for i in range(4):
    plt.clf()
    plt.axes([0.17, 0.1, 0.75, 0.8])
    pp = np.linspace(0, 1, df.shape[0])
    plt.plot(pp, np.sort(df.iloc[:, i]))
    plt.grid(True)
    plt.xlabel("Probability point", size=15)
    plt.ylabel(df.columns[i] + " quantile", size=15)
    pdf.savefig()

ent = pd.read_csv("entropy_minute.csv", header=None)
plt.clf()
plt.plot(ent)
plt.grid(True)
plt.xlabel("Minutes", size=15)
plt.ylabel("Destination port entropy", size=15)
pdf.savefig()


# Return ICC for minutes within hours.  A high ICC means that the
# variation between minutes is much greater than the variation within
# minutes.
def anova(x, m):
    y = np.reshape(x, (-1, m))  # hours by minutes
    w = y.var(1).mean()
    b = y.mean(1).var()
    t = y.var()
    return b / t


for x in df.Traffic, df.Sources, df.TCP, df.UDP:
    x = np.asarray(x)
    print("%10.3f %10.3f" % (anova(x, 60), anova(x, 240)))


def kt(z, k):
    n = len(z)
    x = z[0:n - k]
    y = z[k:n]
    return kendalltau(x, y).correlation


f = [[], [], [], []]
for j in range(4):
    for k in range(1, 240):
        f[j].append(kt(df.iloc[:, j], k))
    f[j] = np.asarray(f[j])

plt.clf()
plt.grid(True)
plt.plot(f[0], label=df.columns[0])
plt.plot(f[1], label=df.columns[1])
plt.plot(f[2], label=df.columns[2])
plt.plot(f[3], label=df.columns[3])
plt.xlabel("Minutes", size=15)
plt.ylabel("Tau-autocorrelation", size=15)
ha, lb = plt.gca().get_legend_handles_labels()
leg = plt.figlegend(ha, lb, "upper center", ncol=4)
leg.draw_frame(False)
pdf.savefig()


def hurst(x):
    z = []
    for m in 15, 30, 60:
        y = np.reshape(x, (-1, m))
        v = y.mean(1).var()
        z.append([m, v])
    z = np.log(np.asarray(z))
    c = np.cov(z.T)
    b = c[0, 1] / c[0, 0]
    return b / 2 + 1


def hurstabs(x):
    z = []
    for m in 15, 30, 60:
        y = np.reshape(x, (-1, m))
        v = np.mean(np.abs(y.mean(1)))
        z.append([m, v])
    z = np.log(np.asarray(z))
    c = np.cov(z.T)
    b = c[0, 1] / c[0, 0]
    return b + 1


for x in df.Traffic, df.Sources, df.UDP, df.TCP:
    x = np.log(np.asarray(x))
    x -= x.mean()
    h = hurst(x)
    print("%.3f %.3f" % (hurst(x), hurstabs(x)))

from numpy.lib.stride_tricks import as_strided
import statsmodels.api as sm

labs = ["Traffic", "Sources", "UDP", "TCP"]
for j, x in enumerate([df.Traffic, df.Sources, df.UDP, df.TCP]):
    x = np.asarray(x)
    x = np.log(x)
    x -= x.mean()
    z = as_strided(x, shape=(len(x) - 30, 30), strides=(8, 8))
    y = z[:, 0]
    x = z[:, 1:30]
    # alphas, active, coefs = linear_model.lars_path(x, y, method='lars')
    params = []
    for alpha in 0.0001, 0.0002:
        result = sm.OLS(y, x).fit_regularized(alpha=0.1, L1_wt=0.1)
        params.append(result.params)

    plt.clf()
    plt.title(labs[j])
    for p in params:
        plt.plot(p)
    plt.xlabel("Lag", size=15)
    plt.ylabel("Coefficient", size=15)
    plt.grid(True)
    plt.ylim(-1, 1)
    pdf.savefig()

pdf.close()
