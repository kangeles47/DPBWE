# Let's play with rotations for a little bit:
                #theta = radians(self.hasOrientation)
                #zrot_mat = np.array([[cos(theta), -sin(theta), 0], [sin(theta), cos(theta), 0], [0, 0, 1]])
                #roof_pts = new_zpts[-1]
                #roof_pts = [Point(0,0,0), Point()]
                #rotate_x = []
                #rotate_y = []
                #rotate_z = []
                #for pt in roof_pts:
                    # Create an array with the points x, y, z:
                    #vec = np.array([[pt.x], [pt.y], [pt.z]])
                    # Rotate x, y about z plane:
                    #rpts = zrot_mat.dot(vec)
                    # Save these as a new point:
                    #rotate_x.append(rpts[0][0])
                    #rotate_y.append(rpts[1][0])
                    #rotate_z.append(rpts[2][0])
                # Plot the rotated x, y pairs:
                #plt.plot(rotate_x, rotate_y)
                #plt.show()