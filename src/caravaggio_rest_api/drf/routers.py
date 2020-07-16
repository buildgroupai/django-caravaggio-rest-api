# -*- coding: utf-8 -*
# Copyright (c) 2019 BuildGroup Data Services Inc.
# All rights reserved.
# This software is proprietary and confidential and may not under
# any circumstances be used, copied, or distributed.
from rest_framework import routers
from rest_framework.routers import flatten, Route, DynamicRoute, ImproperlyConfigured

VALID_ACTIONS_FOR_LIST = {"list": "get", "create": "post"}

VALID_ACTIONS_FOR_DETAIL = {"retrieve": "get", "update": "put", "partial_update": "patch", "destroy": "delete"}


class CaravaggioRouter(routers.DefaultRouter):
    def __init__(self, actions=None, *args, **kwargs):
        """
        Configure the available routes based on the informed actions.

        All the dynamic routes are always registered. Dynamic routes are
        generated based on the use of @action(detail=True) decorator on
        methods of the viewset.

        :param actions: the actions the router should register. The valid
            actions are: list, retrieve, create, update, partial_update,
            and destroy
        """
        # if actions is None, we register all the available operations
        if actions is None:
            actions = list(VALID_ACTIONS_FOR_LIST.keys()) + list(VALID_ACTIONS_FOR_DETAIL)

        if not isinstance(actions, (list, set)):
            raise TypeError(
                "The `actions` argument must be a list or set."
                "For example "
                "`CaravaggiokRouter(['list', 'retrieve'])`"
            )

        list_actions = {}
        detail_actions = {}

        list_actions_keys = VALID_ACTIONS_FOR_LIST.keys()
        detail_actions_keys = VALID_ACTIONS_FOR_DETAIL.keys()

        for action in actions:
            if action in list_actions_keys:
                list_actions[VALID_ACTIONS_FOR_LIST[action]] = action
            elif action in detail_actions_keys:
                detail_actions[VALID_ACTIONS_FOR_DETAIL[action]] = action

        self.custom_routes = [
            # List route.
            routers.Route(
                url=r"^{prefix}{trailing_slash}$",
                mapping=list_actions,
                name="{basename}-list",
                detail=False,
                initkwargs={"suffix": "List"},
            ),
            # Dynamically generated list routes. Generated using
            # @action(detail=False) decorator on methods of the viewset.
            routers.DynamicRoute(
                url=r"^{prefix}/{url_path}{trailing_slash}$", name="{basename}-{url_name}", detail=False, initkwargs={}
            ),
            # Detail route.
            routers.Route(
                url=r"^{prefix}/{lookup}{trailing_slash}$",
                mapping=detail_actions,
                name="{basename}-detail",
                detail=True,
                initkwargs={"suffix": "Instance"},
            ),
            # Dynamically generated detail routes. Generated using
            # @action(detail=True) decorator on methods of the viewset.
            routers.DynamicRoute(
                url=r"^{prefix}/{lookup}/{url_path}{trailing_slash}$",
                name="{basename}-{url_name}",
                detail=True,
                initkwargs={},
            ),
        ]

        super().__init__(*args, **kwargs)

    def get_routes(self, viewset):
        """
        Augment `self.routes` with any dynamically generated routes.

        Returns a list of the Route namedtuple.
        """
        # converting to list as iterables are good for one pass, known
        # host needs to be checked again and again for
        # different functions.
        known_actions = list(
            flatten([route.mapping.values() for route in self.custom_routes if isinstance(route, Route)])
        )

        extra_actions = viewset.get_extra_actions()

        # checking action names against the known actions list
        not_allowed = [action.__name__ for action in extra_actions if action.__name__ in known_actions]
        if not_allowed:
            msg = "Cannot use the @action decorator on the following " "methods, as they are existing routes: %s"
            raise ImproperlyConfigured(msg % ", ".join(not_allowed))

        # partition detail and list actions
        detail_actions = [action for action in extra_actions if action.detail]
        list_actions = [action for action in extra_actions if not action.detail]

        routes = []
        for route in self.custom_routes:
            if isinstance(route, DynamicRoute) and route.detail:
                routes += [self._get_dynamic_route(route, action) for action in detail_actions]
            elif isinstance(route, DynamicRoute) and not route.detail:
                routes += [self._get_dynamic_route(route, action) for action in list_actions]
            else:
                routes.append(route)

        return routes
