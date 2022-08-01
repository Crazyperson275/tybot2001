import routines
from tools import *
from objects import *
from routines import *
from tmcp import TMCPHandler, TMCPMessage, ActionType


#This file is for strategy
class ExampleBot(GoslingAgent):
    def __init__(self, name, team, index):
        super().__init__(name, team, index)
        self.step = None

    def get_boost(agent):

        large_boosts = [boost for boost in agent.boosts if boost.large and boost.active]
        closest = large_boosts[0]
        closest_distance = (large_boosts[0].location - agent.me.location).magnitude()
        for item in large_boosts:

            item_distance = (item.location - agent.me.location).magnitude()
            if item_distance < closest_distance:
                closest = item

                closest_distance = item_distance
        agent.push(goto_boost(closest, agent.ball.location))

    def goal_boost(agent):
        boosts = [boost for boost in agent.boosts if boost.large and boost.active and abs(
            agent.friend_goal.location.y - boost.location.y) - 200 < abs(agent.friend_goal.location).magnitude()]

        if len(boosts) > 0:
            closest = boosts[0]

            for boost in boosts:

                if (boost.location - agent.me.location).magnitude() < (closest.location - agent.me.location).magnitude():
                    closest = boost
            agent.push(goto_boost(closest, agent.friend_goal.location))

    def shots(agent, left_side, right_side, next_shot=False):

        left_back_post = False
        right_back_post = False

        targets = {"goal": (left_side, right_side)}
        shots = find_hits(agent, targets)

        if len(shots["goal"]) > 0:
            shot = shots["goal"][0]
            for shot_type in shots:
                shot_list = shots[shot_type]
                for s in shot_list:
                    try:
                        if s.is_aerial():
                            print("aerial shot")
                    except:
                        print(s)
            agent.push(shot)

        else:
            if next_shot:
                agent.push(short_shot(agent.foe_goal.location))
            elif not next_shot:
                agent.push(go_goal(agent, agent.ball.location))

    def run(agent):

        score_chance = abs(agent.ball.location - agent.foe_goal.location).magnitude() <= 1500

        mid = Vector3(0,0,0)
        need_clear = abs(agent.ball.location - agent.friend_goal.location).magnitude() <= 5500
        ball_close_to_net = abs(agent.ball.location - agent.friend_goal.location).magnitude() <= 3500

        left_post = agent.friend_goal.left_post + Vector3(300,500,0) * -side(agent.team)
        right_post = agent.friend_goal.right_post + Vector3(-300,500,0) * -side(agent.team)
        ball_right = agent.ball.location.x >= 0
        ball_left = agent.ball.location.x < 0

        foe_right_side = agent.foes[0].location.x >= 0
        foe_left_side = agent.foes[0].location.x < 0

        my_goal_to_ball, my_ball_distance = (agent.ball.location - agent.friend_goal.location).normalize(True)
        goal_to_me = agent.me.location - agent.friend_goal.location
        my_distance = my_goal_to_ball.dot(goal_to_me)

        foe_goal_to_ball, foe_ball_distance = (agent.ball.location - agent.foe_goal.location).normalize(True)
        foe_goal_to_foe = agent.foes[0].location - agent.foe_goal.location
        foe_distance = foe_goal_to_ball.dot(foe_goal_to_foe)

        me_onside = my_distance - 200 < my_ball_distance
        foe_onside = foe_distance - 200 < foe_ball_distance

        super_close = (agent.me.location - agent.ball.location).magnitude() < 750
        close = (agent.me.location - agent.ball.location).magnitude() < 3000
        foe_super_close = (agent.foes[0].location - agent.ball.location).magnitude() < 750
        foe_close = (agent.foes[0].location - agent.ball.location).magnitude() < 3000
        have_boost = agent.me.boost > 10

        left_back_post = False
        right_back_post = False
        return_to_goal = False

        if agent.team == 0:
            agent.debug_stack()
            agent.line(agent.friend_goal.location, agent.ball.location, [255, 255, 255])
            my_point = agent.friend_goal.location + (my_goal_to_ball * my_distance)
            agent.line(my_point - Vector3(0, 0, 100), my_point + Vector3(0, 0, 100), [0, 255, 0])

        if len(agent.stack) < 1:
            if agent.kickoff_flag:
                agent.push(kickoff(agent))

            elif me_onside and need_clear and not foe_super_close:
                agent.push(short_shot(agent.foe_goal.location))

            elif score_chance and close:
                agent.shots(agent.foe_goal.left_post, agent.foe_goal.left_post, True)

            elif not score_chance and agent.me.boost < 20 and not foe_super_close:
                agent.get_boost()

            elif not foe_onside and close and me_onside and not foe_close:
                agent.shots(agent.foe_goal.left_post, agent.foe_goal.right_post)

            elif foe_onside and not me_onside and foe_super_close and not close:
                agent.push(go_goal(agent, agent.ball.location))

            elif me_onside and not foe_close and foe_right_side and foe_onside:
                agent.shots(agent.foe_goal.left_post, agent.foe_goal.location)

            elif me_onside and not foe_close and foe_left_side and foe_onside:
                agent.shots(agent.foe_goal.location, agent.foe_goal.right_post)

            elif not me_onside and not have_boost and not foe_close:
                agent.goal_boost()

            elif not me_onside and foe_onside:
                agent.push(go_goal(agent, agent.ball.location))

            elif not have_boost and not foe_close:
                agent.get_boost()

            else:
                agent.shots(agent.foe_goal.left_post, agent.foe_goal.right_post)

        if return_to_goal:
            distance_to_goal = abs(agent.friend_goal.location.y) - abs(agent.me.location.y)
            relative_target = agent.friend_goal.location - agent.me.location
            angles = defaultPD(agent, agent.me.local(relative_target))
            defaultThrottle(agent, 2300)
            agent.controller.boost = False if abs(angles[1]) > .5 or agent.me.airborne else agent.controller.boost
            agent.controller.handbrake = True if abs(angles[1]) > 2.8 else False