package com.example.user.controller;

import com.example.common.api.UserApi;
import com.example.common.dto.UserDTO;
import com.example.user.service.UserService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RestController
public class UserController implements UserApi {

    @Autowired
    private UserService userService;

    @Override
    public List<UserDTO> list() {
        return userService.listAll();
    }

    @Override
    public UserDTO getById(Long id) {
        return userService.getById(id);
    }

    @Override
    public UserDTO create(UserDTO user) {
        return userService.create(user);
    }
}