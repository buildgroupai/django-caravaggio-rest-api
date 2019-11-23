# -*- coding: utf-8 -*
# Copyright (c) 2019 BuildGroup Data Services Inc.
# All rights reserved.
# This software is proprietary and confidential and may not under
# any circumstances be used, copied, or distributed.
from rest_framework import routers

VALID_ACTIONS_FOR_LIST = {
    "list": "get",
    "create": "post"
}

VALID_ACTIONS_FOR_DETAIL = {
    "retrieve": "get",
    "update": "put",
    "partial_update": "patch",
    "destroy": "delete"
}


class CaravaggiokRouter(routers.DefaultRouter):

    routes = []

    def __init__(self, actions=None, *args, **kwargs):
        """
        Configure the available routes based on the informed actions.

        All the dynamic routes are always registered. Dynamic routes are
        generated based on the use of @action(detail=True) decorator on
        methods of the viewset.

        :param actions: the actions the router should register. The valid
            actions are: lest, retrieve, create, update, partial_update,
            and destroy
        """
        # if actions is None, we register all the available operations
        if not actions:
            actions = list(VALID_ACTIONS_FOR_LIST.keys()) + \
                      list(VALID_ACTIONS_FOR_DETAIL)

        if not isinstance(actions, (list, set)):
            raise TypeError("The `actions` argument must be a list or set."
                            "For example "
                            "`CaravaggiokRouter(['list', 'retrieve'])`")

        list_actions = {}
        detail_actions = {}

        list_actions_keys = VALID_ACTIONS_FOR_LIST.keys()
        detail_actions_keys = VALID_ACTIONS_FOR_DETAIL.keys()

        for action in actions:
            if action in list_actions_keys:
                list_actions[VALID_ACTIONS_FOR_LIST[action]] = action
            elif action in detail_actions_keys:
                detail_actions[VALID_ACTIONS_FOR_DETAIL[action]] = action

        self.routes.extend([
            # List route.
            routers.Route(
                url=r'^{prefix}{trailing_slash}$',
                mapping=list_actions,
                name='{basename}-list',
                detail=False,
                initkwargs={'suffix': 'List'}
            ),
            # Dynamically generated list routes. Generated using
            # @action(detail=False) decorator on methods of the viewset.
            routers.DynamicRoute(
                url=r'^{prefix}/{url_path}{trailing_slash}$',
                name='{basename}-{url_name}',
                detail=False,
                initkwargs={}
            ),
            # Detail route.
            routers.Route(
                url=r'^{prefix}/{lookup}{trailing_slash}$',
                mapping=detail_actions,
                name='{basename}-detail',
                detail=True,
                initkwargs={'suffix': 'Instance'}
            ),
            # Dynamically generated detail routes. Generated using
            # @action(detail=True) decorator on methods of the viewset.
            routers.DynamicRoute(
                url=r'^{prefix}/{lookup}/{url_path}{trailing_slash}$',
                name='{basename}-{url_name}',
                detail=True,
                initkwargs={}
            )
        ])

        super().__init__(*args, **kwargs)
