import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
from matplotlib.collections import PatchCollection
import numpy as np
import matplotlib.animation as anim
import matplotlib.patches as mpatches



class RobotPath:
    def __init__(self, x, color, robot_path, robot_pre_suf_time, workspace, ap):
        self.robot_path = robot_path
        self.robot_pre_suf_time = robot_pre_suf_time
        self.i_x = np.asarray(x, dtype=float)
        self.color = np.asarray(color, dtype=float)
        self.x = self.i_x.copy()
        self.elapse_time = -3  # adjust this number to display time recorder from 0s
        self.dt = 1
        self.workspace = workspace
        self.ap = ap
        self.sat = dict()

    def iterate(self):
        robot_point = {}
        self.elapse_time += self.dt
        elapse_time = self.elapse_time
        x = []
        for type_robot, path in self.robot_path.items():
            if elapse_time >= len(path) - 1:
                # robot stays put
                if round(self.robot_pre_suf_time[type_robot][0]) == round(self.robot_pre_suf_time[type_robot][1]):
                    x.append((path[-1][0]+0.5, path[-1][1]+0.5))
                else:
                    t = (int(np.floor(elapse_time)) - self.robot_pre_suf_time[type_robot][0]) % \
                    (self.robot_pre_suf_time[type_robot][1] - self.robot_pre_suf_time[type_robot][0])
                    first = self.robot_path[type_robot][self.robot_pre_suf_time[type_robot][0]+t]
                    second = self.robot_path[type_robot][self.robot_pre_suf_time[type_robot][0]+t+1]
                    x.append((first[0]+(second[0]-first[0]) * (elapse_time - np.floor(elapse_time)) + 0.5,
                              first[1]+(second[1]-first[1]) * (elapse_time - np.floor(elapse_time)) + 0.5))
            else:
                first = self.robot_path[type_robot][int(np.floor(elapse_time))]
                second = self.robot_path[type_robot][int(np.floor(elapse_time)+1)]
                x.append((first[0] + (second[0] - first[0]) * (elapse_time - np.floor(elapse_time)) + 0.5,
                          first[1] + (second[1] - first[1]) * (elapse_time - np.floor(elapse_time)) + 0.5))

            robot_point[type_robot] = x[-1]
        self.x = np.array(x)
        self.label(robot_point)

    def label(self, robot_point):
        true_ap = dict()
        # loop over each conjunction in the task formula
        for aps in self.ap:
            sat = True
            robot = []
            for ap in aps:
                # robot of certain type that visits the specified region
                r = [type_robot[1]+1 for type_robot, location in robot_point.items() if type_robot[0] == ap[1]
                     and (location[0]-0.5, location[1]-0.5) == self.workspace.regions[ap[0]]]
                # whether the conjunction is satisfied
                if len(r) < ap[2]:
                    sat = False
                    break
                robot.append(r)
            if sat:
                # (location, type): #robots
                true_ap.update({(ap[0], ap[1]): robot[index] for index, ap in enumerate(aps)})

        if true_ap and self.elapse_time != -1:
            self.sat = true_ap


def plot_workspace(workspace, ax):
    plt.rc('text', usetex=False)
    ax.set_xlim((0, workspace.width))
    ax.set_ylim((0, workspace.length))
    plt.xticks(np.arange(0, workspace.width + 1, 5))
    plt.yticks(np.arange(0, workspace.length + 1, 5))
    plot_workspace_helper(ax, workspace.regions, 'region')
    plot_workspace_helper(ax, workspace.obstacles, 'obstacle')
    # plt.grid(visible=True, which='major', color='gray', linestyle='--')

    # plt.title(r'$\phi_3$')


def plot_workspace_helper(ax, obj, obj_label):
    plt.rc('text', usetex=False)
    plt.rc('font', family='serif')
    plt.gca().set_aspect('equal', adjustable='box')
    # p0 dock
    # p1 grocery p2 health p3 outdors p4 pet p5 furniture p6 electronics 
    # p7 packing area
    region = {'p0': 'dock',
              'p1': 'grocery',
              'p2': 'health',
              'p3': 'outdoor',
              'p4': 'pet supplies',
              'p5': 'furniture',
              'p6': 'electronics',
              'p7': 'packing area'}
    for key in obj:
        if 'r' in key:
            continue
        # color = 'gray' if obj_label != 'region' else 'white'
        color = 'gray' if obj_label != 'region' or (key == 'p0' or key == 'p7') else 'green'
        alpha = 0.6 if obj_label != 'region' or (key == 'p0' or key == 'p7') else 0.1
        for grid in obj[key]:
            x_ = grid[0]
            y_ = grid[1]
            x = []
            y = []
            patches = []
            for point in [(x_, y_), (x_ + 1, y_), (x_ + 1, y_ + 1), (x_, y_ + 1)]:
                x.append(point[0])
                y.append(point[1])
            polygon = Polygon(np.column_stack((x, y)), closed=True)
            patches.append(polygon)
            p = PatchCollection(patches, facecolors=color, edgecolors=color, linewidths=0.2, alpha=alpha)
            ax.add_collection(p)
        # ax.text(np.mean(x) - 0.2, np.mean(y) - 0.2, r'${}_{{{}}}$'.format(key[0], key[1:]), fontsize=12)
        if key == 'p0':
            ax.text(np.mean(x) + 1, np.mean(y) - 5, r'{}'.format(region[key]), fontsize=6)
        elif key == 'p7':
            ax.text(np.mean(x) - 3.5, np.mean(y) + 1, r'{}'.format(region[key]), fontsize=6)
        elif 'o' in key:
            ax.text(np.mean(x) - 2, np.mean(y) + 1, r'{}'.format(region['p' + key[1:]]), fontsize=6)



def animate(i, ax, particles, annots, cls_robot_path, time_template, time_text, ap_template, ap_text):
    cls_robot_path.iterate()
    time_text.set_text(time_template % cls_robot_path.elapse_time)
    # ap_text.set_text(ap_template % cls_robot_path.)
    for t, new_x_i, new_y_i in zip(annots, cls_robot_path.x[:, 0], cls_robot_path.x[:, 1]):
        t.set_position((new_x_i, new_y_i+0.1))

    particles.set_offsets(cls_robot_path.x)
    particles.set_array(cls_robot_path.color)

    for ap, location_type, robot in zip(ap_text[:len(cls_robot_path.sat.keys())], cls_robot_path.sat.keys(),
                                        cls_robot_path.sat.values()):
        ap.set_text(ap_template.format(robot, 'of type {0}'.format(location_type[1]),
                                       'visit {0}'.format(location_type[0][1:])))
    for ap in ap_text[len(cls_robot_path.sat.keys()):]:
        ap.set_text(ap_template.format('{0}'.format("."), '{0}'.format("."), '{0}'.format(".")))

    return [particles]+annots+[time_text]+ap_text


def vis(task, case, workspace, robot_path, robot_pre_suf_time, ap):
    num_type = len(workspace.type_num.keys())
    colors_type = np.linspace(0.9, 0.1, num_type)
    # color = [0.4, 0.6]
    x = list((value[0]+0.5, value[1]+0.5) for value in workspace.type_robot_location.values())
    colors = [colors_type[i[0]-1] for i in robot_path.keys()]

    cls_robot_path = RobotPath(x, colors, robot_path, robot_pre_suf_time, workspace, ap)

    fig = plt.figure()
    ax = fig.add_subplot(111)
    # ax.yaxis.tick_right()
    plot_workspace(workspace, ax)

    time_template = 'time = %.1fs'
    time_text = ax.text(0.01, 1.05, time_template % cls_robot_path.elapse_time, transform=ax.transAxes)

    ap_template = '{0} {1} {2}'
    # ap_text = [ax.text(-3.5, 9.5 - k*0.5, ap_template.format('{0}'.format("."), '{0}'.format("."), '{0}'.format(".")),
    #                    color='red', weight='bold') for k in range(10)]
    ap_text = []
    cls_robot_path.label(workspace.type_robot_location)
    groups = ["type1", "type2", "type3"]
    particles = ax.scatter([], [], c=[], s=30, cmap="hsv", vmin=0, vmax=1)
    # Create a legend patch for each group
    legend_patches = [mpatches.Patch(color=plt.cm.hsv(color), label=group) for group, color in zip(groups, colors_type)]
    # Add the legend patches to the plot
    ax.legend(handles=legend_patches, fontsize=6)
    # annots = [ax.text(100, 100, r"[{0},{1}]".format(type_robot[1]+1, type_robot[0]), weight='bold', fontsize=8)
    #           for type_robot in robot_path.keys()]
    annots = [ax.text(100, 100, r"{0}".format(type_robot[1]+1), weight='bold', fontsize=8)
              for type_robot in robot_path.keys()]

    max_frame = max(2 * time[1] - time[0] for time in robot_pre_suf_time.values())/cls_robot_path.dt + 1
    ani = anim.FuncAnimation(fig, animate, fargs=[ax, particles, annots, cls_robot_path, time_template, time_text,
                                                  ap_template, ap_text],
                             frames=int(np.ceil(max_frame)), interval=30, blit=True)
    # ani.save('/Users/chrislaw/Box Sync/Research/LTL_MRTA_icra2020/video/phi.mp4', fps=1/cls_robot_path.dt, dpi=400)
    ani.save(f'./data/mapp_{task}_{case}.mp4', fps=2/cls_robot_path.dt, dpi=400)

    # plt.show()