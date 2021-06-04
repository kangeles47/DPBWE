# Create decision trees to characterize missile environment and consequent debris trajectories
    # Might want to include here consideration of roof assembly condition (age)
    # Typical debris types: roof covers, roof sheathing, frame/joist elements (e.g., timber)
# Develop rulesets for site-specific debris classification for range of common typologies
# Map debris classes to appropriate trajectory models
# Develop decision trees to extract relevant component data from manufacturer's specifications to refine site-specific debris models
# Implement similitude parameters to project source building damage


def get_trajectory(bldg, debris_class, wind_speed, debris_mass):
    air_density = 1.225  # kg/m^3
    gravity = 9.81  # m/s^2
    tachikawa_num = air_density*(wind_speed**2)/(2*debris_mass*gravity)
    # Find flight time and coefficients for the debris class:
    if debris_class == 'sheet':
        from scipy.stats import uniform
        flight_time = uniform(1, 2.5)  # This will be a uniform distribution
        c = 0.91
        c1 = -0.148
        c2 = 0.024
        c3 = -0.0014
    elif debris_class == 'rod':
        c = 0.801
        mean_flight = 2
        sigma_flight = 0.4
        # Define a truncated Gaussian or lognormal variable to sample from
    elif debris_class == 'compact':
        pass
    alongwind_dist = (2*debris_mass/air_density)*((0.5*c*(tachikawa_num*flight_time)**2) + (c1*(tachikawa_num*flight_time)**3) + (c2*(tachikawa_num*flight_time)**4) + (c3*(tachikawa_num*flight_time)**5))
    acrosswind_dist = 0
    sigma_along = 0.35*alongwind_dist
    sigma_across = 0.35*alongwind_dist
    return alongwind_dist, acrosswind_dist, sigma_along, sigma_across, tachikawa_num, c, gravity


def calc_impact_momentum(debris_mass, debris_area, horiz_impact_vel):
    return debris_mass* debris_area* horiz_impact_vel


def get_horiz_impact_vel(wind_speed, c, tachikawa_num, gravity, horiz_fdist):
    from math import exp, sqrt
    x = gravity*horiz_fdist/(wind_speed**2)
    horiz_impact_vel = wind_speed*(1-exp(-1*sqrt(2*c*tachikawa_num*x)))
    return horiz_impact_vel

def get_debris_class(bldg):
    # To determine debris class, roof material composition will need to be known:
    compact_types = ['gravel']
    sheet_types = ['metal']
    rod_types = ['frame', 'joist']
    if bldg.hasElement['Roof'][0].hasCover:
        debris_class = None
    return debris_class


def get_mass_unit_area(bldg):
    # Derive mass per unit area values for each debris type from regional manufacturers
    if bldg.hasLocation['State'] == 'FL':
        if bldg.hasLocation['County'] == 'Bay':
            pass