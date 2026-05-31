using Microsoft.AspNetCore.Mvc;
using System.Collections.Generic;

namespace StoreApi.API.Controllers;

[ApiController]
[Route("[controller]")]
public class UserController : ControllerBase
{
    [HttpGet]
    public ActionResult<List<UserDto>> GetAll()
    {
        return Ok(new List<UserDto>());
    }

    [HttpGet("{id}")]
    public ActionResult<UserDto> GetById(Guid id)
    {
        return Ok(new UserDto());
    }

    [HttpPost]
    public ActionResult<UserDto> Create(UserDto request)
    {
        return CreatedAtAction(nameof(GetById), new { id = request.Id }, request);
    }
}
