using Microsoft.AspNetCore.Mvc;
using System.Collections.Generic;
using System.Linq;
using StoreApi.API.Dtos;
using StoreApi.Domain.Entities;
using StoreApi.Domain.Repositories;

namespace StoreApi.API.Controllers;

[ApiController]
[Route("[controller]")]
public class UserController : ControllerBase
{
    private readonly IUserRepository _userRepository;

    public UserController(IUserRepository userRepository)
    {
        _userRepository = userRepository;
    }

    [HttpGet]
    public ActionResult<List<UserDto>> GetAll()
    {
        var entities = _userRepository.GetAll().Select(ToDto).ToList();
        return Ok(entities);
    }

    [HttpGet("{id}")]
    public ActionResult<UserDto> GetById(Guid id)
    {
        var entity = _userRepository.GetById(id);
        if (entity is null)
        {
            return NotFound();
        }

        return Ok(ToDto(entity));
    }

    [HttpPost]
    public ActionResult<UserDto> Create(UserDto request)
    {
        var entity = ToEntity(request);
        _userRepository.Create(entity);
        return CreatedAtAction(nameof(GetById), new { id = entity.Id }, ToDto(entity));
    }

    [HttpPut("{id}")]
    public IActionResult Update(Guid id, UserDto request)
    {
        var entity = ToEntity(request);
        entity.Id = id;
        _userRepository.Update(entity);
        return NoContent();
    }

    [HttpDelete("{id}")]
    public IActionResult Delete(Guid id)
    {
        var existingEntity = _userRepository.GetById(id);
        if (existingEntity is null)
        {
            return NotFound();
        }

        _userRepository.Delete(id);
        return NoContent();
    }

    private static UserDto ToDto(User entity)
    {
        return new UserDto
        {
            Id = entity.Id,
            Email = entity.Email,
        };
    }

    private static User ToEntity(UserDto dto)
    {
        return new User
        {
            Id = dto.Id,
            Email = dto.Email,
        };
    }
}
